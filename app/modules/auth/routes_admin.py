from flask import Blueprint, current_app, g, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_limiter.util import get_remote_address

from app.core.db import transaction
from app.core.errors import ValidationError
from app.core.http import json_body, no_content, ok
from app.core.validation import trim
from app.extensions import limiter
from app.modules.auth import service
from app.modules.auth.decorators import admin_required

MIN_PASSWORD = 10
MSG_PASSWORD = f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres"

bp = Blueprint("auth_admin", __name__, url_prefix="/api/admin")

def _login_key() -> str:
    data = request.get_json(silent=True)
    correo = trim(data.get("correo")).lower() if isinstance(data, dict) else ""
    return f"{get_remote_address()}:{correo}"

def _expires_in() -> int:
    return int(current_app.config["JWT_ACCESS_MINUTES"]) * 60

@bp.post("/login")
@limiter.limit("5 per minute", key_func=_login_key)
def login():
    data = json_body()
    with transaction() as conn:
        result = service.login(conn, trim(data.get("correo")), data.get("password") or "", _expires_in())
    return ok(result)

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return ok(service.refresh(get_jwt_identity(), _expires_in()))

@bp.get("/me")
@admin_required
def me():
    return ok(g.admin)

@bp.post("/me/password")
@admin_required
def change_password():
    data = json_body()
    nueva = data.get("nueva")
    if not isinstance(nueva, str) or len(nueva) < MIN_PASSWORD:
        raise ValidationError({"nueva": MSG_PASSWORD})
    with transaction() as conn:
        service.change_password(conn, g.admin["id"], data.get("actual") or "", nueva)
    return no_content()
