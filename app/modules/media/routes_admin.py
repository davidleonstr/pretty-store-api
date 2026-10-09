from flask import Blueprint, current_app, g, request

from app.core.db import transaction
from app.core.errors import NotFound, PayloadTooLarge, ValidationError
from app.core.http import created, json_body, no_content, ok
from app.core.pagination import get_page_params
from app.core.validation import parse_uuid, trim
from app.modules.auth import admin_required
from app.modules.media import schemas, service

bp = Blueprint("media_admin", __name__, url_prefix="/api/admin/images")

def _id_or_404(value: str) -> str:
    uid = parse_uuid(value)
    if not uid:
        raise NotFound("Imagen no encontrada")
    return uid

@bp.post("")
@admin_required
def upload():
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ValidationError({"file": "Selecciona una imagen"})
    max_bytes = int(current_app.config["MAX_UPLOAD_MB"]) * 1024 * 1024
    raw = file.stream.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise PayloadTooLarge(f"La imagen no puede pasar de {current_app.config['MAX_UPLOAD_MB']} MB")
    alt = trim(request.form.get("alt", ""))[:300]
    with transaction() as conn:
        row = service.upload(conn, raw, file.filename, alt, g.admin["id"])
    return created(schemas.to_admin(row))

@bp.get("")
@admin_required
def list_images():
    page, page_size, limit, offset = get_page_params()
    rows, total = service.list_images(limit, offset)
    return ok({"items": [schemas.to_admin(r) for r in rows], "page": page, "pageSize": page_size, "total": total})

@bp.patch("/<image_id>")
@admin_required
def update_image(image_id):
    alt = schemas.parse_alt(json_body())
    with transaction() as conn:
        row = service.update_alt(conn, _id_or_404(image_id), alt)
    return ok(schemas.to_admin(row))

@bp.delete("/<image_id>")
@admin_required
def delete_image(image_id):
    with transaction() as conn:
        service.delete_image(conn, _id_or_404(image_id))
    return no_content()
