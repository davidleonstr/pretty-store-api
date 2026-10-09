from datetime import date

from app.core.db import execute, fetch_all, fetch_one

_PICKUP_COLS = "id, name, address, lat, lon, is_active, sort_order, created_at, updated_at"
_PICKUP_UPDATABLE = {"name", "address", "lat", "lon", "is_active", "sort_order"}
_FECHA_UPDATABLE = {"fecha", "dia_id", "is_active", "sort_order"}

# ---- Puntos ---------------------------------------------------------------------
def list_pickups(conn) -> list[dict]:
    return fetch_all(conn, f"SELECT {_PICKUP_COLS} FROM pickups ORDER BY sort_order ASC, created_at ASC")

def get_pickup(conn, pickup_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {_PICKUP_COLS} FROM pickups WHERE id = :id", {"id": pickup_id})

def insert_pickup(conn, pickup_id, name, address, lat, lon, is_active, sort_order) -> dict:
    return fetch_one(
        conn,
        f"""INSERT INTO pickups (id, name, address, lat, lon, is_active, sort_order)
            VALUES (:id, :name, :address, :lat, :lon, :active, :sort) RETURNING {_PICKUP_COLS}""",
        {"id": pickup_id, "name": name, "address": address, "lat": lat, "lon": lon,
         "active": is_active, "sort": sort_order},
    )

def update_pickup(conn, pickup_id: str, changes: dict) -> None:
    cols = [c for c in changes if c in _PICKUP_UPDATABLE]
    if cols:
        sets = ", ".join(f"{c} = :{c}" for c in cols)
        execute(conn, f"UPDATE pickups SET {sets} WHERE id = :id", {**{c: changes[c] for c in cols}, "id": pickup_id})

def delete_pickup(conn, pickup_id: str) -> int:
    return execute(conn, "DELETE FROM pickups WHERE id = :id", {"id": pickup_id})

def pickup_has_orders(conn, pickup_id: str) -> bool:
    """Lectura sobre `orders` solo para validar borrados."""
    row = fetch_one(
        conn,
        """SELECT 1 AS x FROM orders o
           JOIN pickup_fecha_horas fh ON fh.id = o.pickup_fecha_hora_id
           JOIN pickup_fechas f ON f.id = fh.pickup_fecha_id
           WHERE f.pickup_id = :id LIMIT 1""",
        {"id": pickup_id},
    )
    return row is not None

def list_sin_horarios(conn) -> list[dict]:
    return fetch_all(conn, "SELECT id, name FROM v_pickups_sin_horarios ORDER BY name")

# ---- Fechas ---------------------------------------------------------------------
def list_fechas(conn, pickup_ids: list[str] | None = None) -> list[dict]:
    sql = """SELECT f.id, f.pickup_id, f.fecha, f.dia_id, d.nombre AS dia, f.is_active, f.sort_order
             FROM pickup_fechas f JOIN dias d ON d.id = f.dia_id"""
    params = {}
    if pickup_ids is not None:
        sql += " WHERE f.pickup_id = ANY(:ids)"
        params["ids"] = list(pickup_ids)
    return fetch_all(conn, sql + " ORDER BY f.pickup_id, f.fecha ASC, f.sort_order ASC", params)

def get_fecha(conn, pickup_id: str, fecha_id: str) -> dict | None:
    return fetch_one(
        conn,
        """SELECT f.id, f.pickup_id, f.fecha, f.dia_id, d.nombre AS dia, f.is_active, f.sort_order
           FROM pickup_fechas f JOIN dias d ON d.id = f.dia_id
           WHERE f.id = :f AND f.pickup_id = :p""",
        {"f": fecha_id, "p": pickup_id},
    )

def fecha_exists(conn, pickup_id: str, fecha: date, exclude_id: str | None = None) -> bool:
    row = fetch_one(
        conn,
        """SELECT 1 AS x FROM pickup_fechas
           WHERE pickup_id = :p AND fecha = :f AND (CAST(:ex AS uuid) IS NULL OR id <> CAST(:ex AS uuid))""",
        {"p": pickup_id, "f": fecha, "ex": exclude_id},
    )
    return row is not None

def insert_fecha(conn, pickup_id: str, fecha: date, dia_id: int, is_active: bool, sort_order: int) -> str:
    row = fetch_one(
        conn,
        """INSERT INTO pickup_fechas (pickup_id, fecha, dia_id, is_active, sort_order)
           VALUES (:p, :f, :d, :a, :s) RETURNING id""",
        {"p": pickup_id, "f": fecha, "d": dia_id, "a": is_active, "s": sort_order},
    )
    return str(row["id"])

def update_fecha(conn, fecha_id: str, changes: dict) -> None:
    cols = [c for c in changes if c in _FECHA_UPDATABLE]
    if cols:
        sets = ", ".join(f"{c} = :{c}" for c in cols)
        execute(conn, f"UPDATE pickup_fechas SET {sets} WHERE id = :id", {**{c: changes[c] for c in cols}, "id": fecha_id})

def delete_fecha(conn, fecha_id: str) -> int:
    return execute(conn, "DELETE FROM pickup_fechas WHERE id = :id", {"id": fecha_id})

def fecha_has_orders(conn, fecha_id: str) -> bool:
    row = fetch_one(
        conn,
        """SELECT 1 AS x FROM orders o JOIN pickup_fecha_horas fh ON fh.id = o.pickup_fecha_hora_id
           WHERE fh.pickup_fecha_id = :id LIMIT 1""",
        {"id": fecha_id},
    )
    return row is not None

# ---- Slots (pickup_fecha_horas) ---------------------------------------------------
def list_slots(conn, pickup_ids: list[str] | None = None) -> list[dict]:
    sql = """SELECT fh.id AS slot_id, f.id AS fecha_id, f.pickup_id, h.id AS hora_id, h.hora, fh.is_active
             FROM pickup_fecha_horas fh
             JOIN pickup_fechas f ON f.id = fh.pickup_fecha_id
             JOIN horas h ON h.id = fh.hora_id"""
    params = {}
    if pickup_ids is not None:
        sql += " WHERE f.pickup_id = ANY(:ids)"
        params["ids"] = list(pickup_ids)
    return fetch_all(conn, sql + " ORDER BY f.pickup_id, f.fecha, h.hora", params)

def get_slot(conn, fecha_id: str, slot_id: str) -> dict | None:
    return fetch_one(
        conn,
        """SELECT fh.id AS slot_id, fh.pickup_fecha_id AS fecha_id, h.id AS hora_id, h.hora, fh.is_active
           FROM pickup_fecha_horas fh JOIN horas h ON h.id = fh.hora_id
           WHERE fh.id = :s AND fh.pickup_fecha_id = :f""",
        {"s": slot_id, "f": fecha_id},
    )

def slot_exists(conn, fecha_id: str, hora_id: int) -> bool:
    row = fetch_one(
        conn, "SELECT 1 AS x FROM pickup_fecha_horas WHERE pickup_fecha_id = :f AND hora_id = :h",
        {"f": fecha_id, "h": hora_id},
    )
    return row is not None

def insert_slot(conn, fecha_id: str, hora_id: int, is_active: bool = True) -> str:
    row = fetch_one(
        conn,
        "INSERT INTO pickup_fecha_horas (pickup_fecha_id, hora_id, is_active) VALUES (:f, :h, :a) RETURNING id",
        {"f": fecha_id, "h": hora_id, "a": is_active},
    )
    return str(row["id"])

def set_slot_active(conn, slot_id: str, is_active: bool) -> None:
    execute(conn, "UPDATE pickup_fecha_horas SET is_active = :a WHERE id = :id", {"a": is_active, "id": slot_id})

def delete_slot(conn, slot_id: str) -> int:
    return execute(conn, "DELETE FROM pickup_fecha_horas WHERE id = :id", {"id": slot_id})

def slot_has_orders(conn, slot_id: str) -> bool:
    return fetch_one(conn, "SELECT 1 AS x FROM orders WHERE pickup_fecha_hora_id = :id LIMIT 1", {"id": slot_id}) is not None

# ---- Vista de slots (lectura) ---------------------------------------------------------
def list_available_slots(conn) -> list[dict]:
    """Slots disponibles (punto, fecha y slot activos) con datos del punto, para el catálogo público."""
    return fetch_all(
        conn,
        """SELECT s.slot_id, s.pickup_id, s.pickup_name, s.pickup_address, s.fecha, s.dia, s.hora,
                  p.lat, p.lon
           FROM v_pickup_slots s JOIN pickups p ON p.id = s.pickup_id
           WHERE s.disponible
           ORDER BY p.sort_order ASC, p.created_at ASC, s.pickup_id, s.fecha ASC, s.hora ASC""",
    )

def get_slot_view(conn, slot_id: str, lock: bool = False) -> dict | None:
    if lock:
        # FOR SHARE sobre el slot: impide que se desactive o borre mientras se confirma el pedido.
        locked = fetch_one(
            conn, "SELECT id FROM pickup_fecha_horas WHERE id = :id FOR SHARE", {"id": slot_id}
        )
        if not locked:
            return None
    return fetch_one(
        conn,
        """SELECT slot_id, pickup_id, pickup_name, pickup_address, fecha, dia, hora, disponible
           FROM v_pickup_slots WHERE slot_id = :id""",
        {"id": slot_id},
    )
