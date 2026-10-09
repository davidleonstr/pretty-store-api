from app.core.errors import ValidationError
from app.core.http import media_url
from app.core.timeutil import iso_utc
from app.core.validation import is_int, parse_uuid, trim

# ---- Serialización ----------------------------------------------------------
def _photos_public(photos: list[dict], emoji: str) -> list[dict]:
    out = [{"src": media_url(p["storage_key"]), "alt": p["alt_text"]} for p in photos]
    return out or [{"emoji": emoji}]

def to_public(row: dict) -> dict:
    return {
        "slug": row["slug"],
        "name": row["name"],
        "emoji": row["emoji"],
        "priceCents": row["price_cents"],
        "tag": row["tag"],
        "description": row["description"],
        "photos": _photos_public(row.get("photos", []), row["emoji"]),
        "soldOut": row["stock"] == 0,
    }

def to_admin(row: dict) -> dict:
    out = to_public(row)
    out["photos"] = [
        {"id": str(p["image_id"]), "src": media_url(p["storage_key"]), "alt": p["alt_text"]}
        for p in row.get("photos", [])
    ]
    out.update({
        "id": str(row["id"]),
        "isActive": row["is_active"],
        "sortOrder": row["sort_order"],
        "createdAt": iso_utc(row["created_at"]),
        "updatedAt": iso_utc(row["updated_at"]),
        "stock": row["stock"],
        "categoriaId": str(row["categoria_id"]),
    })
    return out

def box_to_public(box: dict, items: list[dict], photos: list[dict]) -> dict:
    """Box compacto para `inBoxes` (misma forma que el Box público de `boxes`)."""
    return {
        "slug": box["slug"],
        "name": box["name"],
        "emoji": box["emoji"],
        "priceCents": box["price_cents"],
        "tag": box["tag"],
        "short": box["short"],
        "description": box["description"],
        "items": [{"slug": i["slug"], "qty": i["qty"]} for i in items],
        "photos": _photos_public(photos, box["emoji"]),
        "soldOut": any(i["stock"] < i["qty"] for i in items),
    }

def availability(row: dict) -> dict:
    sold_out = row["stock"] == 0
    return {"slug": row["slug"], "soldOut": sold_out, "available": not sold_out}

# ---- Validación de entrada ------------------------------------------------------
def _check_common(data: dict, errors: dict, out: dict) -> None:
    if "emoji" in data:
        emoji = trim(data["emoji"])
        if not emoji or len(emoji) > 16:
            errors["emoji"] = "Escribe un emoji válido"
        out["emoji"] = emoji
    if "description" in data:
        if not isinstance(data["description"], str):
            errors["description"] = "La descripción debe ser texto"
        out["description"] = trim(data["description"])
    if "stock" in data:
        if not is_int(data["stock"]) or data["stock"] < 0:
            errors["stock"] = "El stock debe ser un entero mayor o igual a 0"
        out["stock"] = data["stock"]
    if "isActive" in data:
        if not isinstance(data["isActive"], bool):
            errors["isActive"] = "Valor inválido"
        out["is_active"] = data["isActive"]
    if "sortOrder" in data:
        if not is_int(data["sortOrder"]):
            errors["sortOrder"] = "Debe ser un número entero"
        out["sort_order"] = data["sortOrder"]
    if "imageIds" in data:
        if not isinstance(data["imageIds"], list):
            errors["imageIds"] = "Debe ser una lista de imágenes"
        out["image_ids"] = data["imageIds"]

def _check_main(data: dict, errors: dict, out: dict, required: bool) -> None:
    if required or "name" in data:
        name = trim(data.get("name"))
        if not name or len(name) > 120:
            errors["name"] = "Escribe un nombre de hasta 120 caracteres"
        out["name"] = name
    if required or "priceCents" in data:
        price = data.get("priceCents")
        if not is_int(price) or price <= 0:
            errors["priceCents"] = "El precio debe ser un entero mayor que 0 (centavos)"
        out["price_cents"] = price
    if required or "categoriaId" in data:
        cat = parse_uuid(data.get("categoriaId"))
        if not cat:
            errors["categoriaId"] = "Elige una categoría válida"
        out["categoria_id"] = cat

def parse_create(data: dict) -> dict:
    errors, out = {}, {}
    _check_main(data, errors, out, required=True)
    _check_common(data, errors, out)
    if errors:
        raise ValidationError(errors)
    out.setdefault("emoji", "🎁")
    out.setdefault("description", "")
    out.setdefault("stock", 0)
    out.setdefault("is_active", True)
    out.setdefault("sort_order", 0)
    out.setdefault("image_ids", [])
    return out

def parse_update(data: dict) -> dict:
    errors, out = {}, {}
    _check_main(data, errors, out, required=False)
    _check_common(data, errors, out)
    if errors:
        raise ValidationError(errors)
    return out

def parse_stock(data: dict) -> dict:
    has_stock, has_delta = "stock" in data, "delta" in data
    if has_stock == has_delta:
        raise ValidationError({"stock": "Envía solo 'stock' o solo 'delta'"})
    key = "stock" if has_stock else "delta"
    value = data[key]
    if not is_int(value) or (key == "stock" and value < 0):
        raise ValidationError({key: "Debe ser un número entero" if key == "delta" else "El stock debe ser un entero mayor o igual a 0"})
    return {key: value}

def parse_sold_out(value: str | None) -> bool | None:
    if value is None or value == "":
        return None
    if value.lower() in ("true", "1"):
        return True
    if value.lower() in ("false", "0"):
        return False
    raise ValidationError({"soldOut": "Debe ser true o false"})
