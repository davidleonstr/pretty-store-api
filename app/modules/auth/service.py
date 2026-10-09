from flask_jwt_extended import create_access_token, create_refresh_token

from app.core.errors import Unauthorized, ValidationError
from app.core.security import verify_password
from app.modules import administradores

BAD_LOGIN = "Correo o contraseña incorrectos"

def _access(admin_id: str) -> str:
    return create_access_token(identity=admin_id, additional_claims={"role": "admin"})

def login(conn, correo: str, password: str, expires_in: int) -> dict:
    row = administradores.get_by_correo(correo)
    # Se verifica el hash aunque el correo no exista (igualar tiempos).
    valid = verify_password(row["password_hash"] if row else None, password or "")
    if not row or not valid or not row["activo"]:
        raise Unauthorized(BAD_LOGIN)
    admin_id = str(row["id"])
    administradores.record_login(conn, admin_id)
    return {
        "accessToken": _access(admin_id),
        "refreshToken": create_refresh_token(identity=admin_id, additional_claims={"role": "admin"}),
        "tokenType": "Bearer",
        "expiresIn": expires_in,
        "admin": {"id": admin_id, "nombre": row["nombre"], "correo": row["correo"]},
    }

def refresh(admin_id: str, expires_in: int) -> dict:
    if not administradores.get_active(admin_id):
        raise Unauthorized("Sesión inválida o expirada")
    return {"accessToken": _access(admin_id), "expiresIn": expires_in}

def change_password(conn, admin_id: str, actual: str, nueva: str) -> None:
    admin = administradores.get_active(admin_id)
    if not admin:
        raise Unauthorized("Sesión inválida o expirada")
    row = administradores.get_by_correo(admin["correo"])
    if not verify_password(row["password_hash"], actual or ""):
        raise ValidationError({"actual": "La contraseña actual es incorrecta"})
    administradores.set_password(conn, admin_id, nueva)
