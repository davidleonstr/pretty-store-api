from flask import Blueprint

from app.core.db import transaction
from app.core.errors import NotFound
from app.core.http import created, json_body, no_content, ok
from app.core.validation import parse_uuid
from app.modules.auth import admin_required
from app.modules.pickups import schemas, service

bp = Blueprint("pickups_admin", __name__, url_prefix="/api/admin/pickups")

def _uuid_or_404(value: str) -> str:
    uid = parse_uuid(value)
    if not uid:
        raise NotFound("No encontrado")
    return uid

@bp.get("")
@admin_required
def list_pickups():
    return ok([schemas.to_admin(p) for p in service.list_admin()])

@bp.get("/sin-horarios")
@admin_required
def sin_horarios():
    return ok([schemas.sin_horarios_to_admin(r) for r in service.list_sin_horarios()])

@bp.post("")
@admin_required
def create_pickup():
    data = schemas.parse_pickup_create(json_body())
    with transaction() as conn:
        row = service.create_pickup(conn, data)
    return created(schemas.to_admin(row))

@bp.patch("/<pickup_id>")
@admin_required
def update_pickup(pickup_id):
    changes = schemas.parse_pickup_update(json_body())
    with transaction() as conn:
        row = service.update_pickup(conn, pickup_id, changes)
    return ok(schemas.to_admin(row))

@bp.delete("/<pickup_id>")
@admin_required
def delete_pickup(pickup_id):
    with transaction() as conn:
        service.delete_pickup(conn, pickup_id)
    return no_content()

@bp.post("/<pickup_id>/fechas")
@admin_required
def create_fecha(pickup_id):
    data = schemas.parse_fecha_create(json_body())
    with transaction() as conn:
        row = service.create_fecha(conn, pickup_id, data)
    return created(schemas.fecha_to_admin(row))

@bp.patch("/<pickup_id>/fechas/<fecha_id>")
@admin_required
def update_fecha(pickup_id, fecha_id):
    changes = schemas.parse_fecha_update(json_body())
    with transaction() as conn:
        row = service.update_fecha(conn, pickup_id, _uuid_or_404(fecha_id), changes)
    return ok(schemas.fecha_to_admin(row))

@bp.delete("/<pickup_id>/fechas/<fecha_id>")
@admin_required
def delete_fecha(pickup_id, fecha_id):
    with transaction() as conn:
        service.delete_fecha(conn, pickup_id, _uuid_or_404(fecha_id))
    return no_content()

@bp.post("/<pickup_id>/fechas/<fecha_id>/horas")
@admin_required
def create_slot(pickup_id, fecha_id):
    hora_id = schemas.parse_slot_create(json_body())
    with transaction() as conn:
        row = service.create_slot(conn, pickup_id, _uuid_or_404(fecha_id), hora_id)
    return created(schemas.slot_to_admin(row))

@bp.patch("/<pickup_id>/fechas/<fecha_id>/horas/<slot_id>")
@admin_required
def update_slot(pickup_id, fecha_id, slot_id):
    is_active = schemas.parse_slot_update(json_body())
    with transaction() as conn:
        row = service.update_slot(conn, pickup_id, _uuid_or_404(fecha_id), _uuid_or_404(slot_id), is_active)
    return ok(schemas.slot_to_admin(row))

@bp.delete("/<pickup_id>/fechas/<fecha_id>/horas/<slot_id>")
@admin_required
def delete_slot(pickup_id, fecha_id, slot_id):
    with transaction() as conn:
        service.delete_slot(conn, pickup_id, _uuid_or_404(fecha_id), _uuid_or_404(slot_id))
    return no_content()
