from app.core.db import execute, fetch_all, fetch_one

_COLS = "id, nombre, correo::text AS correo, activo, ultimo_login_at, created_at, updated_at"

def get_by_id(conn, admin_id: str) -> dict | None:
    return fetch_one(conn, f"SELECT {_COLS} FROM administradores WHERE id = :id", {"id": admin_id})

def get_by_correo_with_hash(conn, correo: str) -> dict | None:
    return fetch_one(
        conn,
        f"SELECT {_COLS}, password_hash FROM administradores WHERE correo = :correo",
        {"correo": correo},
    )

def list_all(conn) -> list[dict]:
    return fetch_all(conn, f"SELECT {_COLS} FROM administradores ORDER BY created_at ASC")

def exists_correo(conn, correo: str, exclude_id: str | None = None) -> bool:
    row = fetch_one(
        conn,
        "SELECT 1 AS x FROM administradores WHERE correo = :correo AND (CAST(:ex AS uuid) IS NULL OR id <> CAST(:ex AS uuid))",
        {"correo": correo, "ex": exclude_id},
    )
    return row is not None

def count_active(conn, exclude_id: str | None = None) -> int:
    row = fetch_one(
        conn,
        "SELECT count(*) AS n FROM administradores WHERE activo AND (CAST(:ex AS uuid) IS NULL OR id <> CAST(:ex AS uuid))",
        {"ex": exclude_id},
    )
    return row["n"]

def insert(conn, nombre: str, correo: str, password_hash: str) -> dict:
    return fetch_one(
        conn,
        f"INSERT INTO administradores (nombre, correo, password_hash) VALUES (:n, :c, :p) RETURNING {_COLS}",
        {"n": nombre, "c": correo, "p": password_hash},
    )

def update(conn, admin_id: str, nombre=None, activo=None, password_hash=None) -> dict | None:
    return fetch_one(
        conn,
        f"""UPDATE administradores SET
              nombre = COALESCE(:n, nombre),
              activo = COALESCE(:a, activo),
              password_hash = COALESCE(:p, password_hash)
            WHERE id = :id RETURNING {_COLS}""",
        {"id": admin_id, "n": nombre, "a": activo, "p": password_hash},
    )

def update_login(conn, admin_id: str) -> None:
    execute(conn, "UPDATE administradores SET ultimo_login_at = now() WHERE id = :id", {"id": admin_id})

def delete(conn, admin_id: str) -> int:
    return execute(conn, "DELETE FROM administradores WHERE id = :id", {"id": admin_id})
