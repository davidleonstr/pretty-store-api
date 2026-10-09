from datetime import datetime

from app.core.db import execute, fetch_all, fetch_one

# ---- Escrituras ---------------------------------------------------------------
def insert_order(conn, code: str, kind: str, cliente_id: str, nota: str, slot_id: str, total_cents: int) -> str:
    row = fetch_one(
        conn,
        """INSERT INTO orders (code, kind, cliente_id, nota, pickup_fecha_hora_id, total_cents)
           VALUES (:code, CAST(:kind AS order_kind), :cliente, :nota, :slot, :total) RETURNING id""",
        {"code": code, "kind": kind, "cliente": cliente_id, "nota": nota, "slot": slot_id, "total": total_cents},
    )
    return str(row["id"])

def insert_item(conn, order_id: str, product_id: str | None, box_id: str | None, name: str,
                unit_price_cents: int, qty: int) -> None:
    execute(
        conn,
        """INSERT INTO order_items (order_id, product_id, box_id, name, unit_price_cents, qty)
           VALUES (:o, :p, :b, :n, :u, :q)""",
        {"o": order_id, "p": product_id, "b": box_id, "n": name, "u": unit_price_cents, "q": qty},
    )

def update_fields(conn, order_id: str, cliente_id: str, nota: str, slot_id: str) -> None:
    execute(
        conn,
        "UPDATE orders SET cliente_id = :c, nota = :n, pickup_fecha_hora_id = :s WHERE id = :id",
        {"c": cliente_id, "n": nota, "s": slot_id, "id": order_id},
    )

def set_status(conn, order_id: str, status: str, delivered_at: datetime | None) -> None:
    execute(
        conn,
        "UPDATE orders SET status = CAST(:s AS order_status), delivered_at = :d WHERE id = :id",
        {"s": status, "d": delivered_at, "id": order_id},
    )

# ---- Lecturas -----------------------------------------------------------------
def lock_order(conn, order_id: str) -> dict | None:
    """Bloquea la fila del pedido (FOR UPDATE) para comprobar el estado dentro de la transacción."""
    return fetch_one(
        conn,
        "SELECT id, status, delivered_at FROM orders WHERE id = :id FOR UPDATE",
        {"id": order_id},
    )

def get_id_by_code(conn, code: str) -> str | None:
    row = fetch_one(conn, "SELECT id FROM orders WHERE code = :c", {"c": code})
    return str(row["id"]) if row else None

def get_view(conn, order_id: str) -> dict | None:
    return fetch_one(conn, "SELECT * FROM v_orders_retiro WHERE id = :id", {"id": order_id})

def get_view_by_code(conn, code: str) -> dict | None:
    return fetch_one(conn, "SELECT * FROM v_orders_retiro WHERE code = :c", {"c": code})

def list_items(conn, order_id: str) -> list[dict]:
    return fetch_all(
        conn,
        """SELECT id, product_id, box_id, name, unit_price_cents, qty
           FROM order_items WHERE order_id = :id ORDER BY name, id""",
        {"id": order_id},
    )

def _filters(status, kind, q, ts_from, ts_to) -> tuple[str, dict]:
    where, params = [], {}
    if status:
        where.append("status = CAST(:status AS order_status)")
        params["status"] = status
    if kind:
        where.append("kind = CAST(:kind AS order_kind)")
        params["kind"] = kind
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where.append(
            "(code ILIKE :q OR (nombres || ' ' || apellidos) ILIKE :q OR correo::text ILIKE :q OR celular ILIKE :q)"
        )
        params["q"] = f"%{escaped}%"
    if ts_from:
        where.append("created_at >= :ts_from")
        params["ts_from"] = ts_from
    if ts_to:
        where.append("created_at < :ts_to")
        params["ts_to"] = ts_to
    return (" WHERE " + " AND ".join(where)) if where else "", params

def list_admin(conn, status, kind, q, ts_from, ts_to, limit: int, offset: int) -> list[dict]:
    where, params = _filters(status, kind, q, ts_from, ts_to)
    params.update({"limit": limit, "offset": offset})
    return fetch_all(
        conn,
        f"SELECT * FROM v_orders_retiro{where} ORDER BY created_at DESC, id LIMIT :limit OFFSET :offset",
        params,
    )

def count_admin(conn, status, kind, q, ts_from, ts_to) -> int:
    where, params = _filters(status, kind, q, ts_from, ts_to)
    return fetch_one(conn, f"SELECT count(*) AS n FROM v_orders_retiro{where}", params)["n"]
