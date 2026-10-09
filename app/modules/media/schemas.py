from app.core.errors import ValidationError
from app.core.http import media_url
from app.core.timeutil import iso_utc
from app.core.validation import trim

def to_admin(row: dict) -> dict:
    out = {
        "id": str(row["id"]),
        "src": media_url(row["storage_key"]),
        "alt": row["alt_text"],
        "width": row["width"],
        "height": row["height"],
        "sizeBytes": row["size_bytes"],
        "createdAt": iso_utc(row["created_at"]),
    }
    if "used_products" in row:
        out["usedBy"] = {"products": row["used_products"], "boxes": row["used_boxes"]}
    return out

def parse_alt(data: dict) -> str:
    alt = data.get("alt", "")
    if not isinstance(alt, str):
        raise ValidationError({"alt": "El texto alternativo debe ser texto"})
    alt = trim(alt)
    if len(alt) > 300:
        raise ValidationError({"alt": "El texto alternativo no puede pasar de 300 caracteres"})
    return alt
