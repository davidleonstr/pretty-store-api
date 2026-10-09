import uuid

from app.core import db
from app.core.errors import Conflict, NotFound, ValidationError
from app.core.validation import parse_uuid
from app.modules.media import processing, repository as repo, storage

# ---- API pública (2.6) ---------------------------------------------------
def ensure_exist(image_ids) -> list[str]:
    """Valida una lista de ids de imagen; 422 si alguna no es uuid o no existe."""
    if not isinstance(image_ids, list):
        raise ValidationError({"imageIds": "Debe ser una lista de imágenes"})
    ids = [parse_uuid(i) for i in image_ids]
    if any(i is None for i in ids) or len(set(ids)) != len(ids):
        raise ValidationError({"imageIds": "Alguna imagen no es válida"})
    if ids:
        with db.connection() as conn:
            if repo.count_existing(conn, ids) != len(ids):
                raise ValidationError({"imageIds": "Alguna imagen no existe"})
    return ids

# ---- Operaciones admin ---------------------------------------------------
def upload(conn, raw: bytes, original_name: str | None, alt: str, admin_id: str) -> dict:
    img = processing.process_image(raw)
    storage_key = f"{uuid.uuid4()}.{img.ext}"
    storage.save(storage_key, img.data)
    try:
        return repo.insert(conn, storage_key, (original_name or "")[:255] or None, img.mime_type,
                           len(img.data), img.width, img.height, alt, admin_id)
    except Exception:
        storage.delete(storage_key)
        raise

def list_images(limit: int, offset: int) -> tuple[list[dict], int]:
    with db.connection() as conn:
        return repo.list_page(conn, limit, offset), repo.count_all(conn)

def update_alt(conn, image_id: str, alt: str) -> dict:
    row = repo.update_alt(conn, image_id, alt)
    if not row:
        raise NotFound("Imagen no encontrada")
    return row

def delete_image(conn, image_id: str) -> None:
    row = repo.get_by_id(conn, image_id)
    if not row:
        raise NotFound("Imagen no encontrada")
    if repo.is_used(conn, image_id):
        raise Conflict("in_use", "La imagen está en uso por un producto o una caja")
    repo.delete(conn, image_id)
    storage.delete(row["storage_key"])
