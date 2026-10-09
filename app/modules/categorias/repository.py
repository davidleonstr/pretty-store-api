from app.core.db import execute, fetch_all, fetch_one

_COLS = "id, nombre, sort_order"

def list_all(conn) -> list[dict]:
    return fetch_all(
        conn,
        """SELECT c.id, c.nombre, c.sort_order,
                  (SELECT count(*) FROM products p WHERE p.categoria_id = c.id) AS product_count
           FROM categorias c ORDER BY c.sort_order ASC, lower(c.nombre) ASC""",
    )

def get_by_id(conn, categoria_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {_COLS} FROM categorias WHERE id = :id", {"id": categoria_id})

def exists_id(conn, categoria_id: str) -> bool:
    return fetch_one(conn, "SELECT 1 AS x FROM categorias WHERE id = :id", {"id": categoria_id}) is not None

def exists_nombre(conn, nombre: str, exclude_id: str | None = None) -> bool:
    row = fetch_one(
        conn,
        "SELECT 1 AS x FROM categorias WHERE lower(nombre) = lower(:n) AND (CAST(:ex AS uuid) IS NULL OR id <> CAST(:ex AS uuid))",
        {"n": nombre, "ex": exclude_id},
    )
    return row is not None

def has_products(conn, categoria_id: str) -> bool:
    return fetch_one(conn, "SELECT 1 AS x FROM products WHERE categoria_id = :id LIMIT 1", {"id": categoria_id}) is not None

def insert(conn, nombre: str, sort_order: int) -> dict:
    return fetch_one(
        conn,
        f"INSERT INTO categorias (nombre, sort_order) VALUES (:n, :s) RETURNING {_COLS}",
        {"n": nombre, "s": sort_order},
    )

def update(conn, categoria_id: str, nombre=None, sort_order=None) -> dict | None:
    return fetch_one(
        conn,
        f"""UPDATE categorias SET nombre = COALESCE(:n, nombre), sort_order = COALESCE(:s, sort_order)
            WHERE id = :id RETURNING {_COLS}""",
        {"id": categoria_id, "n": nombre, "s": sort_order},
    )

def delete(conn, categoria_id: str) -> int:
    return execute(conn, "DELETE FROM categorias WHERE id = :id", {"id": categoria_id})
