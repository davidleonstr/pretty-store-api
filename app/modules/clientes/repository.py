from app.core.db import fetch_one

def upsert(conn, nombres: str, apellidos: str, celular: str, correo: str) -> str:
    """Cliente por correo: crea o actualiza nombres, apellidos y celular. Devuelve su id."""
    row = fetch_one(
        conn,
        """INSERT INTO clientes (nombres, apellidos, celular, correo)
           VALUES (:n, :a, :c, :e)
           ON CONFLICT (correo) DO UPDATE
             SET nombres = EXCLUDED.nombres, apellidos = EXCLUDED.apellidos, celular = EXCLUDED.celular
           RETURNING id""",
        {"n": nombres, "a": apellidos, "c": celular, "e": correo},
    )
    return str(row["id"])
