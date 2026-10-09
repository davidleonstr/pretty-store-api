from app.core.db import execute, fetch_all, fetch_one

_BASE = """
SELECT p.id, p.slug, p.name, p.emoji, p.price_cents, p.categoria_id, c.nombre AS tag,
       p.description, p.stock, p.is_active, p.sort_order, p.created_at, p.updated_at
FROM products p
JOIN categorias c ON c.id = p.categoria_id
"""
_ORDER = " ORDER BY p.sort_order ASC, p.created_at ASC"

_UPDATABLE = {"slug", "name", "emoji", "price_cents", "categoria_id", "description", "stock", "is_active", "sort_order"}

# ---- Lecturas ---------------------------------------------------------------
def list_products(conn, only_active: bool, q_slug: str | None = None, tag: str | None = None,
                  sold_out: bool | None = None) -> list[dict]:
    where, params = [], {}
    if only_active:
        where.append("p.is_active")
    if q_slug:
        where.append("p.slug LIKE '%' || :q || '%'")
        params["q"] = q_slug
    if tag:
        where.append("lower(c.nombre) = lower(:tag)")
        params["tag"] = tag
    if sold_out is True:
        where.append("p.stock = 0")
    elif sold_out is False:
        where.append("p.stock > 0")
    sql = _BASE + (" WHERE " + " AND ".join(where) if where else "") + _ORDER
    return fetch_all(conn, sql, params)

def get_by_id(conn, product_id: str) -> dict | None:
    return fetch_one(conn, _BASE + " WHERE p.id = :id", {"id": product_id})

def get_by_slug(conn, slug: str, only_active: bool = True) -> dict | None:
    return fetch_one(conn, _BASE + " WHERE p.slug = :s" + (" AND p.is_active" if only_active else ""), {"s": slug})

def get_by_slugs(conn, slugs: list[str], only_active: bool = True) -> list[dict]:
    if not slugs:
        return []
    sql = _BASE + " WHERE p.slug = ANY(:slugs)" + (" AND p.is_active" if only_active else "") + _ORDER
    return fetch_all(conn, sql, {"slugs": list(slugs)})

def get_by_ids(conn, ids: list[str]) -> list[dict]:
    if not ids:
        return []
    return fetch_all(conn, _BASE + " WHERE p.id = ANY(CAST(:ids AS uuid[]))" + _ORDER, {"ids": list(ids)})

def get_photos(conn, product_ids: list[str]) -> list[dict]:
    if not product_ids:
        return []
    return fetch_all(
        conn,
        """SELECT pi.product_id, i.id AS image_id, i.storage_key, i.alt_text, pi.position
           FROM product_images pi JOIN images i ON i.id = pi.image_id
           WHERE pi.product_id = ANY(CAST(:ids AS uuid[]))
           ORDER BY pi.product_id, pi.position""",
        {"ids": list(product_ids)},
    )

def slug_exists(conn, slug: str, exclude_id: str | None = None) -> bool:
    row = fetch_one(
        conn,
        "SELECT 1 AS x FROM products WHERE slug = :s AND (CAST(:ex AS uuid) IS NULL OR id <> CAST(:ex AS uuid))",
        {"s": slug, "ex": exclude_id},
    )
    return row is not None

# ---- Stock ------------------------------------------------------------------
def lock_for_update(conn, ids: list[str]) -> list[dict]:
    """Bloquea las filas (orden por id, evita interbloqueos)."""
    if not ids:
        return []
    return fetch_all(
        conn,
        "SELECT id, slug, stock FROM products WHERE id = ANY(CAST(:ids AS uuid[])) ORDER BY id FOR UPDATE",
        {"ids": list(ids)},
    )

def set_stock(conn, product_id: str, stock: int) -> None:
    execute(conn, "UPDATE products SET stock = :s WHERE id = :id", {"id": product_id, "s": stock})

# ---- Escrituras ---------------------------------------------------------------
def insert(conn, slug, name, emoji, price_cents, categoria_id, description, stock, is_active, sort_order) -> str:
    row = fetch_one(
        conn,
        """INSERT INTO products (slug, name, emoji, price_cents, categoria_id, description, stock, is_active, sort_order)
           VALUES (:slug, :name, :emoji, :price, :cat, :desc, :stock, :active, :sort) RETURNING id""",
        {"slug": slug, "name": name, "emoji": emoji, "price": price_cents, "cat": categoria_id,
         "desc": description, "stock": stock, "active": is_active, "sort": sort_order},
    )
    return str(row["id"])

def update(conn, product_id: str, changes: dict) -> None:
    cols = [c for c in changes if c in _UPDATABLE]  # lista blanca → seguro interpolar nombres
    if not cols:
        return
    sets = ", ".join(f"{c} = :{c}" for c in cols)
    params = {c: changes[c] for c in cols}
    params["id"] = product_id
    execute(conn, f"UPDATE products SET {sets} WHERE id = :id", params)

def set_images(conn, product_id: str, image_ids: list[str]) -> None:
    execute(conn, "DELETE FROM product_images WHERE product_id = :id", {"id": product_id})
    for pos, image_id in enumerate(image_ids):
        execute(
            conn,
            "INSERT INTO product_images (product_id, image_id, position) VALUES (:p, :i, :pos)",
            {"p": product_id, "i": image_id, "pos": pos},
        )

def delete(conn, product_id: str) -> int:
    return execute(conn, "DELETE FROM products WHERE id = :id", {"id": product_id})

# ---- Lecturas de solo lectura sobre tablas de cajas (JOIN permitido) -------------
def boxes_using(conn, product_id: str) -> list[dict]:
    return fetch_all(
        conn,
        """SELECT b.slug, b.name FROM box_items bi JOIN boxes b ON b.id = bi.box_id
           WHERE bi.product_id = :id ORDER BY b.name""",
        {"id": product_id},
    )

def active_boxes_containing(conn, product_id: str) -> list[dict]:
    return fetch_all(
        conn,
        """SELECT b.id, b.slug, b.name, b.emoji, b.price_cents, t.nombre AS tag, b.short, b.description
           FROM box_items bi
           JOIN boxes b ON b.id = bi.box_id
           JOIN caja_tipos t ON t.id = b.tipo_id
           WHERE bi.product_id = :id AND b.is_active
           ORDER BY b.sort_order ASC, b.created_at ASC""",
        {"id": product_id},
    )

def box_items_with_stock(conn, box_ids: list[str]) -> list[dict]:
    if not box_ids:
        return []
    return fetch_all(
        conn,
        """SELECT bi.box_id, p.slug, bi.qty, p.stock
           FROM box_items bi JOIN products p ON p.id = bi.product_id
           WHERE bi.box_id = ANY(CAST(:ids AS uuid[]))
           ORDER BY bi.box_id, bi.position""",
        {"ids": list(box_ids)},
    )

def box_photos(conn, box_ids: list[str]) -> list[dict]:
    if not box_ids:
        return []
    return fetch_all(
        conn,
        """SELECT bi.box_id, i.storage_key, i.alt_text
           FROM box_images bi JOIN images i ON i.id = bi.image_id
           WHERE bi.box_id = ANY(CAST(:ids AS uuid[]))
           ORDER BY bi.box_id, bi.position""",
        {"ids": list(box_ids)},
    )
