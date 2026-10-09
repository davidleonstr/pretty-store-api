from flask import Blueprint, send_from_directory

from app.core.errors import NotFound
from app.modules.media import storage

bp = Blueprint("media_public", __name__)

@bp.get("/media/<storage_key>")
def serve(storage_key):
    # <storage_key> no admite "/" → sin subdirectorios; send_from_directory evita path traversal.
    try:
        resp = send_from_directory(storage.upload_dir(), storage_key, max_age=31536000)
    except Exception:
        raise NotFound("Imagen no encontrada")
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp
