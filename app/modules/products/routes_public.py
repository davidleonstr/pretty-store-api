from flask import Blueprint, request

from app.core.http import ok
from app.modules.products import schemas, service

bp = Blueprint("products_public", __name__, url_prefix="/api/products")

@bp.get("")
def list_products():
    rows = service.list_public(request.args.get("q"))
    return ok([schemas.to_public(r) for r in rows])

@bp.get("/<slug>")
def get_product(slug):
    row, in_boxes = service.get_public(slug)
    body = schemas.to_public(row)
    body["inBoxes"] = [schemas.box_to_public(b, items, photos) for b, items, photos in in_boxes]
    return ok(body)

@bp.get("/<slug>/availability")
def availability(slug):
    return ok(schemas.availability(service.get_availability(slug)))
