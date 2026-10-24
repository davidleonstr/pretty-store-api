from functools import partial

from flask import Blueprint, g

from app.core.http import created, json_body, no_content, ok, uuid_or_404
from app.db.session import transaction
from app.dependencies import admin_required
from app.schemas import administradores as schemas
from app.services import administradores as service

bp = Blueprint("administradores_admin", __name__, url_prefix="/api/admin/administradores")

_id_or_404 = partial(uuid_or_404, message="Administrador no encontrado")

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

        
