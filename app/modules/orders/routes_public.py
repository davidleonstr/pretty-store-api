from flask import Blueprint

from app.core.db import transaction
from app.core.http import created, json_body, ok
from app.extensions import limiter
from app.modules.orders import schemas, service

bp = Blueprint("orders_public", __name__, url_prefix="/api/orders")

_manage_limit = limiter.shared_limit("30 per hour", scope="orders_manage")

@bp.post("")
@limiter.limit("10 per hour")
def create_order():
    data = schemas.parse_create(json_body())
    with transaction() as conn:
        res = service.create_order(conn, data)
    return created(schemas.created(res["id"], res["code"], res["total_cents"]))

@bp.get("/<order_id>")
@_manage_limit
def get_order(order_id):
    view, items = service.get_order(order_id)
    return ok(schemas.to_customer_detail(view, items))

@bp.patch("/<order_id>")
@_manage_limit
def update_order(order_id):
    patch = schemas.parse_update(json_body())
    with transaction() as conn:
        view, items = service.update_order(conn, order_id, patch)
    return ok(schemas.to_customer_detail(view, items))

@bp.post("/<order_id>/cancel")
@_manage_limit
def cancel_order(order_id):
    with transaction() as conn:
        view, items = service.cancel_order(conn, order_id)
    return ok(schemas.to_customer_detail(view, items))
