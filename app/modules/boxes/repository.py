from app.core.db import execute, fetch_all, fetch_one

_BASE = """
SELECT b.id, b.slug, b.name, b.emoji, b.price_cents, b.tipo_id, t.nombre AS tag, b.short,
       b.description, b.is_active, b.sort_order, b.created_at, b.updated_at
FROM boxes b
JOIN caja_tipos t ON t.id = b.tipo_id
"""
_ORDER = " ORDER BY b.sort_order ASC, b.created_at ASC"
_UPDATABLE = {"slug", "name", "emoji", "price_cents", "tipo_id", "short", "description", "is_active", "sort_order"}

# ---- Lecturas -----------------------------------------------------------------
def list_boxes(conn, only_active: bool, q_slug: str | None = None, tag: str | None = None) -> list[dict]:
    where, params = [], {}
    if only_active:
        where.append("b.is_active")
    if q_slug:
        where.append("b.slug LIKE '%' || :q || '%'")
        params["q"] = q_slug
    if tag:
        where.append("t.nombre = :tag")  # igualdad exacta con caja_tipos.nombre
        params["tag"] = tag
    return fetch_all(conn, _BASE + (" WHERE " + " AND ".join(where) if where else "") + _ORDER, params)

def get_by_id(conn, box_id: str) -> dict | None:
    return fetch_one(conn, _BASE + " WHERE b.id = :id", {"id": box_id})

def get_by_slug(conn, slug: str, only_active: bool = True) -> dict | None:
    return fetch_one(conn, _BASE + " WHERE b.slug = :s" + (" AND b.is_active" if only_active else ""), {"s": slug})

def get_by_slugs(conn, slugs: list[str], only_active: bool = True) -> list[dict]:
    if not slugs:
        return []
    sql = _BASE + " WHERE b.slug = ANY(:slugs)" + (" AND b.is_active" if only_active else "") + _ORDER
    return fetch_all(conn, sql, {"slugs": list(slugs)})

def slug_exists(conn, slug: str, exclude_id: str | None = None) -> bool:
    row = fetch_one(
        conn,
        "SELECT 1 AS x FROM boxes WHERE slug = :s AND (CAST(:ex AS uuid) IS NULL OR id <> CAST(:ex AS uuid))",
        {"s": slug, "ex": exclude_id},
    )
    return row is not None

def list_items(conn, box_ids: list[str]) -> list[dict]:
    if not box_ids:
        return []
    return fetch_all(
        conn,
        """SELECT box_id, product_id, qty, position FROM box_items
           WHERE box_id = ANY(CAST(:ids AS uuid[])) ORDER BY box_id, position""",
        {"ids": list(box_ids)},
    )

def get_photos(conn, box_ids: list[str]) -> list[dict]:
    if not box_ids:
        return []
    return fetch_all(
        conn,
        """SELECT bi.box_id, i.id AS image_id, i.storage_key, i.alt_text, bi.position
           FROM box_images bi JOIN images i ON i.id = bi.image_id
           WHERE bi.box_id = ANY(CAST(:ids AS uuid[]))
           ORDER BY bi.box_id, bi.position""",
        {"ids": list(box_ids)},
    )

def list_tipos(conn) -> list[dict]:
    return fetch_all(conn, "SELECT id, nombre FROM caja_tipos ORDER BY id")

def tipo_exists(conn, tipo_id: int) -> bool:
    return fetch_one(conn, "SELECT 1 AS x FROM caja_tipos WHERE id = :id", {"id": tipo_id}) is not None

# ---- Escrituras -----------------------------------------------------------------
def insert(conn, slug, name, emoji, price_cents, tipo_id, short, description, is_active, sort_order) -> str:
    row = fetch_one(
        conn,
        """INSERT INTO boxes (slug, name, emoji, price_cents, tipo_id, short, description, is_active, sort_order)
           VALUES (:slug, :name, :emoji, :price, :tipo, :short, :desc, :active, :sort) RETURNING id""",
        {"slug": slug, "name": name, "emoji": emoji, "price": price_cents, "tipo": tipo_id,
         "short": short, "desc": description, "active": is_active, "sort": sort_order},
    )
    return str(row["id"])

def update(conn, box_id: str, changes: dict) -> None:
    cols = [c for c in changes if c in _UPDATABLE]  # lista blanca
    if not cols:
        return
    sets = ", ".join(f"{c} = :{c}" for c in cols)
    params = {c: changes[c] for c in cols}
    params["id"] = box_id
    execute(conn, f"UPDATE boxes SET {sets} WHERE id = :id", params)

def set_items(conn, box_id: str, items: list[dict]) -> None:
    execute(conn, "DELETE FROM box_items WHERE box_id = :id", {"id": box_id})
    for pos, it in enumerate(items):
        execute(
            conn,
            "INSERT INTO box_items (box_id, product_id, qty, position) VALUES (:b, :p, :q, :pos)",
            {"b": box_id, "p": it["product_id"], "q": it["qty"], "pos": pos},
        )

def set_images(conn, box_id: str, image_ids: list[str]) -> None:
    execute(conn, "DELETE FROM box_images WHERE box_id = :id", {"id": box_id})
    for pos, image_id in enumerate(image_ids):
        execute(
            conn,
            "INSERT INTO box_images (box_id, image_id, position) VALUES (:b, :i, :pos)",
            {"b": box_id, "i": image_id, "pos": pos},
        )

def delete(conn, box_id: str) -> int:
    return execute(conn, "DELETE FROM boxes WHERE id = :id", {"id": box_id})
