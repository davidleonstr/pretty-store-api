"""Orquestador de pedidos: combina clientes, pickups, products y boxes en una sola transacción."""
from datetime import datetime, timezone

from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.core.validation import parse_uuid
from app.modules import boxes, clientes, pickups, products
from app.modules.orders import codegen, pricing, repository as repo
from app.modules.orders.schemas import MSG

NOT_FOUND = "Pedido no encontrado"
LOCKED = "Este pedido ya no se puede modificar"

def _uid(conn, key: str) -> str:
    """Id interno a partir del id (uuid) o del código PS-XXXXXX (sin distinguir mayúsculas)."""
    key = (key or "").strip()
    uid = parse_uuid(key)
    if uid:
        return uid
    code = key.upper()
    if codegen.CODE_RE.match(code):
        found = repo.get_id_by_code(conn, code)
        if found:
            return found
    raise NotFound(NOT_FOUND)  # inválido e inexistente responden igual

def _detail(conn, order_id: str) -> tuple[dict, list[dict]]:
    view = repo.get_view(conn, order_id)
    if not view:
        raise NotFound(NOT_FOUND)
    return view, repo.list_items(conn, order_id)

def _stock_needs(conn, order_id: str) -> dict[str, int]:
    """{product_id: qty} que el pedido tiene descontado (cajas: contenido actual × qty)."""
    needs: dict[str, int] = {}
    for it in repo.list_items(conn, order_id):
        if it["product_id"]:
            pid = str(it["product_id"])
            needs[pid] = needs.get(pid, 0) + it["qty"]
        elif it["box_id"]:  # si la caja fue eliminada, box_id es NULL y no repone
            for pid, qty in boxes.get_requirements(str(it["box_id"])).items():
                needs[pid] = needs.get(pid, 0) + qty * it["qty"]
    return needs

# ---- Cliente -------------------------------------------------------------------------
def create_order(conn, data: dict) -> dict:
    errors: dict[str, str] = {}
    resolved = None
    try:
        resolved = pricing.resolve(data["kind"], data["items"])
    except ValidationError as err:
        errors.update(err.fields)

    slot = pickups.get_available_slot(data["hora_id"], data["pickup_id"], conn=conn, lock=True)
    if slot is None:
        errors["horaId"] = MSG["horaId"]
    if errors:
        raise ValidationError(errors)

    c = data["customer"]
    cliente_id = clientes.upsert(conn, c["nombres"], c["apellidos"], c["celular"], c["correo"])
    products.deduct_stock(conn, resolved["stock_needs"])  # 409 out_of_stock → se revierte todo

    def _insert(code: str) -> str:
        return repo.insert_order(conn, code, data["kind"], cliente_id, data["nota"],
                                 str(slot["slot_id"]), resolved["total_cents"])

    order_id, code = codegen.insert_with_unique_code(conn, _insert)
    for line in resolved["lines"]:
        repo.insert_item(conn, order_id, line["product_id"], line["box_id"], line["name"],
                         line["unit_price_cents"], line["qty"])
    return {"id": order_id, "code": code, "total_cents": resolved["total_cents"]}

def get_order(order_id: str) -> tuple[dict, list[dict]]:
    with db.connection() as conn:
        return _detail(conn, _uid(conn, order_id))

def update_order(conn, order_id: str, patch: dict) -> tuple[dict, list[dict]]:
    uid = _uid(conn, order_id)
    locked = repo.lock_order(conn, uid)
    if not locked:
        raise NotFound(NOT_FOUND)
    if locked["status"] != "pendiente":
        raise Conflict("order_locked", LOCKED)
    view = repo.get_view(conn, uid)

    slot_id = str(view["pickup_fecha_hora_id"])
    if "hora_id" in patch:
        slot = pickups.get_available_slot(patch["hora_id"], patch["pickup_id"], conn=conn, lock=True)
        if slot is None:
            raise ValidationError({"horaId": MSG["horaId"]})
        slot_id = str(slot["slot_id"])

    cliente_id = str(view["cliente_id"])
    if "customer" in patch:
        merged = {k: view[k] for k in ("nombres", "apellidos", "celular", "correo")}
        merged.update(patch["customer"])
        cliente_id = clientes.upsert(conn, merged["nombres"], merged["apellidos"], merged["celular"], merged["correo"])

    repo.update_fields(conn, uid, cliente_id, patch.get("nota", view["nota"]), slot_id)
    return _detail(conn, uid)

def cancel_order(conn, order_id: str) -> tuple[dict, list[dict]]:
    uid = _uid(conn, order_id)
    locked = repo.lock_order(conn, uid)
    if not locked:
        raise NotFound(NOT_FOUND)
    if locked["status"] == "cancelado":  # idempotente: no repone otra vez
        return _detail(conn, uid)
    if locked["status"] != "pendiente":
        raise Conflict("order_locked", LOCKED)
    products.restore_stock(conn, _stock_needs(conn, uid))
    repo.set_status(conn, uid, "cancelado", None)
    return _detail(conn, uid)

# ---- Administración ------------------------------------------------------------------
def list_admin(filters: dict, limit: int, offset: int) -> tuple[list[dict], int]:
    args = (filters["status"], filters["kind"], filters["q"], filters["ts_from"], filters["ts_to"])
    with db.connection() as conn:
        return repo.list_admin(conn, *args, limit, offset), repo.count_admin(conn, *args)

def get_admin(order_id: str) -> tuple[dict, list[dict]]:
    return get_order(order_id)

def get_admin_by_code(code: str) -> tuple[dict, list[dict]]:
    code = (code or "").strip().upper()
    if not codegen.CODE_RE.match(code):
        raise NotFound(NOT_FOUND)
    with db.connection() as conn:
        view = repo.get_view_by_code(conn, code)
        if not view:
            raise NotFound(NOT_FOUND)
        return view, repo.list_items(conn, str(view["id"]))

def admin_set_status(conn, order_id: str, new_status: str) -> tuple[dict, list[dict]]:
    uid = _uid(conn, order_id)
    locked = repo.lock_order(conn, uid)
    if not locked:
        raise NotFound(NOT_FOUND)
    old = locked["status"]
    if old == new_status:
        return _detail(conn, uid)

    if new_status == "cancelado":
        products.restore_stock(conn, _stock_needs(conn, uid))
    elif old == "cancelado":
        products.deduct_stock(conn, _stock_needs(conn, uid))  # 409 out_of_stock si no alcanza

    delivered_at = None
    if new_status == "entregado":
        delivered_at = locked["delivered_at"] or datetime.now(timezone.utc)
    repo.set_status(conn, uid, new_status, delivered_at)
    return _detail(conn, uid)
