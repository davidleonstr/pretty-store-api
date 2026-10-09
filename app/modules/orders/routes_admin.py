from flask import Blueprint, request

from app.core.db import transaction
from app.core.http import json_body, ok
from app.core.pagination import get_page_params
from app.modules.auth import admin_required
from app.modules.orders import schemas, service

bp = Blueprint("orders_admin", __name__, url_prefix="/api/admin/orders")

@bp.get("")
@admin_required
def list_orders():
    filters = schemas.parse_admin_filters(request.args)
    page, page_size, limit, offset = get_page_params()
    rows, total = service.list_admin(filters, limit, offset)
    return ok({"items": [schemas.to_admin_summary(r) for r in rows], "page": page,
               "pageSize": page_size, "total": total})

@bp.get("/by-code/<code>")
@admin_required
def get_by_code(code):
    view, items = service.get_admin_by_code(code)
    return ok(schemas.to_admin_detail(view, items))

@bp.get("/<order_id>")
@admin_required
def get_order(order_id):
    view, items = service.get_admin(order_id)
    return ok(schemas.to_admin_detail(view, items))

@bp.patch("/<order_id>/status")
@admin_required
def set_status(order_id):
    status = schemas.parse_status(json_body())
    with transaction() as conn:
        view, items = service.admin_set_status(conn, order_id, status)
    return ok(schemas.to_admin_detail(view, items))
