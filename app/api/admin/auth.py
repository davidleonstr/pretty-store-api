from flask import Blueprint, current_app, g, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_limiter.util import get_remote_address

from app.core.http import json_body, no_content, ok
from app.core.validation import trim
from app.db.session import transaction
from app.dependencies import admin_required, limiter
from app.schemas import auth as schemas
from app.services import auth as service

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
    correo, password = schemas.parse_login(json_body())
    with transaction() as conn:
        result = service.login(conn, correo, password, _expires_in())
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
    actual, nueva = schemas.parse_change_password(json_body())
    with transaction() as conn:
        service.change_password(conn, g.admin["id"], actual, nueva)
    return no_content()

        
