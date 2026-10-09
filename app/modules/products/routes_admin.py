from flask import Blueprint, request

from app.core.db import transaction
from app.core.errors import NotFound
from app.core.http import created, json_body, no_content, ok
from app.core.validation import parse_uuid
from app.modules.auth import admin_required
from app.modules.products import schemas, service

bp = Blueprint("products_admin", __name__, url_prefix="/api/admin/products")

def _id_or_404(value: str) -> str:
    uid = parse_uuid(value)
    if not uid:
        raise NotFound("Producto no encontrado")
    return uid

@bp.get("")
@admin_required
def list_products():
    rows = service.list_admin(
        request.args.get("q"), request.args.get("tag"), schemas.parse_sold_out(request.args.get("soldOut"))
    )
    return ok([schemas.to_admin(r) for r in rows])

@bp.post("")
@admin_required
def create_product():
    data = schemas.parse_create(json_body())
    with transaction() as conn:
        row = service.create_product(conn, data)
    return created(schemas.to_admin(row))

@bp.get("/<product_id>")
@admin_required
def get_product(product_id):
    return ok(schemas.to_admin(service.get_admin(_id_or_404(product_id))))

@bp.patch("/<product_id>")
@admin_required
def update_product(product_id):
    data = schemas.parse_update(json_body())
    with transaction() as conn:
        row = service.update_product(conn, _id_or_404(product_id), data)
    return ok(schemas.to_admin(row))

@bp.patch("/<product_id>/stock")
@admin_required
def update_stock(product_id):
    change = schemas.parse_stock(json_body())
    with transaction() as conn:
        row = service.adjust_stock(conn, _id_or_404(product_id), change)
    return ok(schemas.to_admin(row))

@bp.delete("/<product_id>")
@admin_required
def delete_product(product_id):
    with transaction() as conn:
        service.delete_product(conn, _id_or_404(product_id))
    return no_content()
