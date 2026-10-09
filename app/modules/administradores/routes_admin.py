from flask import Blueprint, g

from app.core.db import transaction
from app.core.errors import NotFound
from app.core.http import created, json_body, no_content, ok
from app.core.validation import parse_uuid
from app.modules.administradores import schemas, service
from app.modules.auth import admin_required

bp = Blueprint("administradores_admin", __name__, url_prefix="/api/admin/administradores")

def _id_or_404(value: str) -> str:
    uid = parse_uuid(value)
    if not uid:
        raise NotFound("Administrador no encontrado")
    return uid

@bp.get("")
@admin_required
def list_admins():
    return ok([schemas.to_admin(r) for r in service.list_admins()])

@bp.post("")
@admin_required
def create_admin():
    data = schemas.parse_create(json_body())
    with transaction() as conn:
        row = service.create_admin(conn, data["nombre"], data["correo"], data["password"])
    return created(schemas.to_admin(row))

@bp.patch("/<admin_id>")
@admin_required
def update_admin(admin_id):
    changes = schemas.parse_update(json_body())
    with transaction() as conn:
        row = service.update_admin(conn, _id_or_404(admin_id), g.admin["id"], changes)
    return ok(schemas.to_admin(row))

@bp.delete("/<admin_id>")
@admin_required
def delete_admin(admin_id):
    with transaction() as conn:
        service.delete_admin(conn, _id_or_404(admin_id), g.admin["id"])
    return no_content()
