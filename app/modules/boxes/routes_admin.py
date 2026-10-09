from flask import Blueprint

from app.core.db import transaction
from app.core.errors import NotFound
from app.core.http import created, json_body, no_content, ok
from app.core.validation import parse_uuid
from app.modules.auth import admin_required
from app.modules.boxes import schemas, service

bp = Blueprint("boxes_admin", __name__, url_prefix="/api/admin")

def _id_or_404(value: str) -> str:
    uid = parse_uuid(value)
    if not uid:
        raise NotFound("Caja no encontrada")
    return uid

@bp.get("/caja-tipos")
@admin_required
def list_tipos():
    return ok([schemas.tipo_to_admin(t) for t in service.list_tipos()])

@bp.get("/boxes")
@admin_required
def list_boxes():
    return ok([schemas.to_admin(b) for b in service.list_admin()])

@bp.post("/boxes")
@admin_required
def create_box():
    data = schemas.parse_create(json_body())
    with transaction() as conn:
        box = service.create_box(conn, data)
    return created(schemas.to_admin_detail(box))

@bp.get("/boxes/<box_id>")
@admin_required
def get_box(box_id):
    return ok(schemas.to_admin_detail(service.get_admin(_id_or_404(box_id))))

@bp.patch("/boxes/<box_id>")
@admin_required
def update_box(box_id):
    data = schemas.parse_update(json_body())
    with transaction() as conn:
        box = service.update_box(conn, _id_or_404(box_id), data)
    return ok(schemas.to_admin_detail(box))

@bp.delete("/boxes/<box_id>")
@admin_required
def delete_box(box_id):
    with transaction() as conn:
        service.delete_box(conn, _id_or_404(box_id))
    return no_content()
