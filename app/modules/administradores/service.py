from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.core.security import hash_password
from app.modules.administradores import repository as repo
from app.modules.administradores import schemas

# ---- API pública (2.6) ---------------------------------------------------
def get_active(admin_id: str) -> dict | None:
    with db.connection() as conn:
        row = repo.get_by_id(conn, admin_id)
    return row if row and row["activo"] else None

def get_by_correo(correo: str) -> dict | None:
    """Incluye password_hash; solo para el login."""
    with db.connection() as conn:
        return repo.get_by_correo_with_hash(conn, (correo or "").strip())

def record_login(conn, admin_id: str) -> None:
    repo.update_login(conn, admin_id)

def set_password(conn, admin_id: str, password: str) -> None:
    if len(password) < schemas.MIN_PASSWORD:
        raise ValidationError({"nueva": schemas.MSG_PASSWORD})
    repo.update(conn, admin_id, password_hash=hash_password(password))

# ---- Operaciones admin ---------------------------------------------------
def list_admins() -> list[dict]:
    with db.connection() as conn:
        return repo.list_all(conn)

def create_admin(conn, nombre: str, correo: str, password: str) -> dict:
    correo = correo.strip().lower()
    if repo.exists_correo(conn, correo):
        raise Conflict("email_taken", "Ya existe un administrador con ese correo")
    return repo.insert(conn, nombre, correo, hash_password(password))

def update_admin(conn, admin_id: str, current_id: str, changes: dict) -> dict:
    row = repo.get_by_id(conn, admin_id)
    if not row:
        raise NotFound("Administrador no encontrado")
    if changes.get("activo") is False and row["activo"]:
        if repo.count_active(conn, exclude_id=admin_id) == 0:
            raise Conflict("last_admin", "No puedes desactivar al último administrador activo")
        if admin_id == current_id:
            raise Conflict("self_deactivate", "No puedes desactivarte a ti mismo")
    pwd = hash_password(changes["password"]) if "password" in changes else None
    return repo.update(conn, admin_id, nombre=changes.get("nombre"), activo=changes.get("activo"), password_hash=pwd)

def delete_admin(conn, admin_id: str, current_id: str) -> None:
    row = repo.get_by_id(conn, admin_id)
    if not row:
        raise NotFound("Administrador no encontrado")
    if admin_id == current_id:
        raise Conflict("self_delete", "No puedes eliminarte a ti mismo")
    if row["activo"] and repo.count_active(conn, exclude_id=admin_id) == 0:
        raise Conflict("last_admin", "No puedes eliminar al último administrador activo")
    repo.delete(conn, admin_id)
