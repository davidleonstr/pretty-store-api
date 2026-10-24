from flask import Blueprint

from app.core.http import created, json_body, no_content, ok
from app.db.session import transaction
from app.dependencies import admin_required
from app.schemas import horas as schemas
from app.services import horas as service

bp = Blueprint("horas_admin", __name__, url_prefix="/api/admin/horas")

@bp.get("")
@admin_required
def list_horas():
    return ok([schemas.to_admin(h) for h in service.list_horas()])

@bp.post("")
@admin_required
def create_hora():
    hora = schemas.parse_create(json_body())
    with transaction() as conn:
        row = service.create_hora(conn, hora)
    return created(schemas.to_admin(row))

@bp.delete("/<int:hora_id>")
@admin_required
def delete_hora(hora_id):
    with transaction() as conn:
        service.delete_hora(conn, hora_id)
    return no_content()

        
