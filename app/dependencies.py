"""Extensiones de Flask y dependencias de petición (autenticación de administradores)."""
from functools import wraps

from flask import g
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, verify_jwt_in_request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.core.errors import Forbidden, Unauthorized
from app.services import administradores

jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
cors = CORS()


def admin_required(fn):
    """Valida JWT, rol admin y que el administrador siga activo en la BD."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "admin":
            raise Forbidden()
        admin = administradores.get_active(claims.get("sub"))
        if not admin:
            raise Unauthorized("Sesión inválida o expirada")
        g.admin = {"id": str(admin["id"]), "nombre": admin["nombre"], "correo": admin["correo"]}
        return fn(*args, **kwargs)

    return wrapper
