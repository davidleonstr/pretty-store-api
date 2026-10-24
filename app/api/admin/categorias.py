from functools import partial

from flask import Blueprint

from app.core.http import created, json_body, no_content, ok, uuid_or_404
from app.db.session import transaction
from app.dependencies import admin_required
from app.schemas import categorias as schemas
from app.services import categorias as service

bp = Blueprint("categorias_admin", __name__, url_prefix="/api/admin/categorias")

_id_or_404 = partial(uuid_or_404, message="Categoría no encontrada")

@bp.get("")
@admin_required
def list_categorias():
    return ok([schemas.to_admin(r) for r in service.list_categorias()])

@bp.post("")
@admin_required
def create_categoria():
    data = schemas.parse_create(json_body())
    with transaction() as conn:
        row = service.create_categoria(conn, data["nombre"], data["sort_order"])
    return created(schemas.to_admin(row))

@bp.patch("/<categoria_id>")
@admin_required
def update_categoria(categoria_id):
    changes = schemas.parse_update(json_body())
    with transaction() as conn:
        row = service.update_categoria(conn, _id_or_404(categoria_id), changes)
    return ok(schemas.to_admin(row))

@bp.delete("/<categoria_id>")
@admin_required
def delete_categoria(categoria_id):
    with transaction() as conn:
        service.delete_categoria(conn, _id_or_404(categoria_id))
    return no_content()

        
