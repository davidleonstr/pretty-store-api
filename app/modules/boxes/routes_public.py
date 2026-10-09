from flask import Blueprint, request

from app.core.http import ok
from app.modules.boxes import schemas, service

bp = Blueprint("boxes_public", __name__, url_prefix="/api/boxes")

@bp.get("")
def list_boxes():
    rows = service.list_public(request.args.get("q"), request.args.get("tag"))
    return ok([schemas.to_public(r) for r in rows])

@bp.get("/tags")
def tags():
    return ok(service.list_tags())

@bp.get("/<slug>")
def get_box(slug):
    return ok(schemas.to_public_detail(service.get_public(slug)))

@bp.get("/<slug>/availability")
def availability(slug):
    data = service.get_availability(slug)
    return ok(schemas.availability(data["slug"], data["missing"]))
