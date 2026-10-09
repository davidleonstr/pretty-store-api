from app.core import db
from app.core.errors import Conflict, NotFound
from app.core.timeutil import hhmm, is_future, slot_label
from app.modules import horas
from app.modules.pickups import repository as repo

# ---- API pública (2.6) ---------------------------------------------------
def get_available_slot(slot_id: str, pickup_id: str, conn=None, lock: bool = False) -> dict | None:
    """Slot disponible (punto/fecha/slot activos), de ese punto y con fecha+hora futura (El Salvador)."""
    def _get(c):
        row = repo.get_slot_view(c, slot_id, lock=lock)
        if not row or not row["disponible"] or row["pickup_id"] != pickup_id:
            return None
        if not is_future(row["fecha"], row["hora"]):
            return None
        return row

    if conn is not None:
        return _get(conn)
    with db.connection() as c:
        return _get(c)

def describe_slot(slot_id: str) -> dict | None:
    with db.connection() as conn:
        row = repo.get_slot_view(conn, slot_id)
    if not row:
        return None
    return {
        "id": row["pickup_id"], "name": row["pickup_name"], "address": row["pickup_address"],
        "horaId": str(row["slot_id"]), "fecha": row["fecha"].isoformat(), "dia": row["dia"],
        "hora": hhmm(row["hora"]), "label": slot_label(row["fecha"], row["hora"]),
    }

# ---- Catálogo público ------------------------------------------------------
def list_public() -> list[dict]:
    with db.connection() as conn:
        rows = repo.list_available_slots(conn)
    pickups: dict[str, dict] = {}
    for r in rows:
        if not is_future(r["fecha"], r["hora"]):
            continue
        p = pickups.setdefault(r["pickup_id"], {
            "id": r["pickup_id"], "name": r["pickup_name"], "address": r["pickup_address"],
            "lat": r["lat"], "lon": r["lon"], "slots": [],
        })
        p["slots"].append(r)
    return list(pickups.values())

# ---- Administración ----------------------------------------------------------
def list_admin() -> list[dict]:
    with db.connection() as conn:
        pickups = repo.list_pickups(conn)
        ids = [p["id"] for p in pickups]
        fechas = repo.list_fechas(conn, ids)
        slots = repo.list_slots(conn, ids)
    for f in fechas:
        f["slots"] = [s for s in slots if str(s["fecha_id"]) == str(f["id"])]
    for p in pickups:
        p["fechas"] = [f for f in fechas if f["pickup_id"] == p["id"]]
    return pickups

def list_sin_horarios() -> list[dict]:
    with db.connection() as conn:
        return repo.list_sin_horarios(conn)

def _pickup_or_404(conn, pickup_id: str) -> dict:
    row = repo.get_pickup(conn, pickup_id)
    if not row:
        raise NotFound("Punto de retiro no encontrado")
    return row

def _fecha_or_404(conn, pickup_id: str, fecha_id: str) -> dict:
    row = repo.get_fecha(conn, pickup_id, fecha_id)
    if not row:
        raise NotFound("Fecha no encontrada")
    return row

def _full_pickup(conn, pickup_id: str) -> dict:
    p = _pickup_or_404(conn, pickup_id)
    fechas = repo.list_fechas(conn, [pickup_id])
    slots = repo.list_slots(conn, [pickup_id])
    for f in fechas:
        f["slots"] = [s for s in slots if str(s["fecha_id"]) == str(f["id"])]
    p["fechas"] = fechas
    return p

def create_pickup(conn, data: dict) -> dict:
    if repo.get_pickup(conn, data["id"]):
        raise Conflict("pickup_exists", "Ya existe un punto de retiro con ese nombre")
    repo.insert_pickup(conn, data["id"], data["name"], data["address"], data["lat"], data["lon"],
                       data["is_active"], data["sort_order"])
    return _full_pickup(conn, data["id"])

def update_pickup(conn, pickup_id: str, changes: dict) -> dict:
    _pickup_or_404(conn, pickup_id)
    repo.update_pickup(conn, pickup_id, changes)
    return _full_pickup(conn, pickup_id)

def delete_pickup(conn, pickup_id: str) -> None:
    _pickup_or_404(conn, pickup_id)
    if repo.pickup_has_orders(conn, pickup_id):
        raise Conflict("has_orders", "El punto tiene pedidos; desactívalo con isActive = false")
    repo.delete_pickup(conn, pickup_id)

def create_fecha(conn, pickup_id: str, data: dict) -> dict:
    _pickup_or_404(conn, pickup_id)
    hora_ids = horas.ensure_exist(data["hora_ids"])
    if repo.fecha_exists(conn, pickup_id, data["fecha"]):
        raise Conflict("fecha_exists", "Ya existe esa fecha en el punto de retiro")
    fecha_id = repo.insert_fecha(conn, pickup_id, data["fecha"], data["fecha"].isoweekday(),
                                 data["is_active"], data["sort_order"])
    for hora_id in hora_ids:
        repo.insert_slot(conn, fecha_id, hora_id)
    return _fecha_full(conn, pickup_id, fecha_id)

def _fecha_full(conn, pickup_id: str, fecha_id: str) -> dict:
    f = _fecha_or_404(conn, pickup_id, fecha_id)
    f["slots"] = [s for s in repo.list_slots(conn, [pickup_id]) if str(s["fecha_id"]) == str(fecha_id)]
    return f

def update_fecha(conn, pickup_id: str, fecha_id: str, changes: dict) -> dict:
    _fecha_or_404(conn, pickup_id, fecha_id)
    if "fecha" in changes:
        if repo.fecha_exists(conn, pickup_id, changes["fecha"], exclude_id=fecha_id):
            raise Conflict("fecha_exists", "Ya existe esa fecha en el punto de retiro")
        changes["dia_id"] = changes["fecha"].isoweekday()
    repo.update_fecha(conn, fecha_id, changes)
    return _fecha_full(conn, pickup_id, fecha_id)

def delete_fecha(conn, pickup_id: str, fecha_id: str) -> None:
    _fecha_or_404(conn, pickup_id, fecha_id)
    if repo.fecha_has_orders(conn, fecha_id):
        raise Conflict("has_orders", "La fecha tiene pedidos; desactívala con isActive = false")
    repo.delete_fecha(conn, fecha_id)

def create_slot(conn, pickup_id: str, fecha_id: str, hora_id: int) -> dict:
    _fecha_or_404(conn, pickup_id, fecha_id)
    horas.ensure_exist([hora_id])
    if repo.slot_exists(conn, fecha_id, hora_id):
        raise Conflict("slot_exists", "Esa hora ya existe en la fecha")
    slot_id = repo.insert_slot(conn, fecha_id, hora_id)
    return repo.get_slot(conn, fecha_id, slot_id)

def update_slot(conn, pickup_id: str, fecha_id: str, slot_id: str, is_active: bool) -> dict:
    _fecha_or_404(conn, pickup_id, fecha_id)
    if not repo.get_slot(conn, fecha_id, slot_id):
        raise NotFound("Hora no encontrada")
    repo.set_slot_active(conn, slot_id, is_active)
    return repo.get_slot(conn, fecha_id, slot_id)

def delete_slot(conn, pickup_id: str, fecha_id: str, slot_id: str) -> None:
    _fecha_or_404(conn, pickup_id, fecha_id)
    if not repo.get_slot(conn, fecha_id, slot_id):
        raise NotFound("Hora no encontrada")
    if repo.slot_has_orders(conn, slot_id):
        raise Conflict("has_orders", "La hora tiene pedidos; desactívala con isActive = false")
    repo.delete_slot(conn, slot_id)
