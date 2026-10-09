from datetime import time

from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.core.validation import is_int
from app.modules.horas import repository as repo

# ---- API pública (2.6) ---------------------------------------------------
def ensure_exist(hora_ids) -> list[int]:
    if not isinstance(hora_ids, list) or not all(is_int(i) for i in hora_ids):
        raise ValidationError({"horaIds": "Debe ser una lista de horas válidas"})
    ids = list(dict.fromkeys(hora_ids))  # quita repetidos conservando el orden
    if ids:
        with db.connection() as conn:
            if repo.count_existing(conn, ids) != len(ids):
                raise ValidationError({"horaIds": "Alguna hora no existe"})
    return ids

# ---- Administración ----------------------------------------------------------
def list_horas() -> list[dict]:
    with db.connection() as conn:
        return repo.list_all(conn)

def create_hora(conn, hora: time) -> dict:
    if repo.exists_hora(conn, hora):
        raise Conflict("hora_exists", "Esa hora ya existe")
    return repo.insert(conn, hora)

def delete_hora(conn, hora_id: int) -> None:
    if not repo.get_by_id(conn, hora_id):
        raise NotFound("Hora no encontrada")
    if repo.is_in_use(conn, hora_id):
        raise Conflict("in_use", "La hora está en uso en algún punto de retiro")
    repo.delete(conn, hora_id)
