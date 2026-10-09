from app.modules.clientes import repository as repo

def upsert(conn, nombres: str, apellidos: str, celular: str, correo: str) -> str:
    """API pública: devuelve el `cliente_id` (el correo identifica al cliente)."""
    return repo.upsert(conn, nombres.strip(), apellidos.strip(), celular.strip(), correo.strip().lower())
