from app.core.errors import ValidationError
from app.core.http import media_url
from app.core.timeutil import iso_utc
from app.core.validation import is_int, parse_uuid, trim

# ---- Serialización ----------------------------------------------------------
def _photos_public(photos: list[dict], emoji: str) -> list[dict]:
    out = [{"src": media_url(p["storage_key"]), "alt": p["alt_text"]} for p in photos]
    return out or [{"emoji": emoji}]

def product_to_public(p: dict) -> dict:
    """Product público (misma forma que el módulo products)."""
    return {
        "slug": p["slug"],
        "name": p["name"],
        "emoji": p["emoji"],
        "priceCents": p["price_cents"],
        "tag": p["tag"],
        "description": p["description"],
        "photos": _photos_public(p.get("photos", []), p["emoji"]),
        "soldOut": p["stock"] == 0,
    }

def to_public(box: dict) -> dict:
    return {
        "slug": box["slug"],
        "name": box["name"],
        "emoji": box["emoji"],
        "priceCents": box["price_cents"],
        "tag": box["tag"],
        "short": box["short"],
        "description": box["description"],
        "items": [{"slug": i["slug"], "qty": i["qty"]} for i in box["items"]],
        "photos": _photos_public(box["photos"], box["emoji"]),
        "soldOut": box["sold_out"],
    }

def to_public_detail(box: dict) -> dict:
    out = to_public(box)
    out["contents"] = [
        {"product": product_to_public(i["product"]), "qty": i["qty"]}
        for i in box["items"] if i["product"]["is_active"]
    ]
    return out

def to_admin(box: dict) -> dict:
    out = to_public(box)
    out["items"] = [{"productId": str(i["product_id"]), "slug": i["slug"], "qty": i["qty"]} for i in box["items"]]
    out["photos"] = [
        {"id": str(p["image_id"]), "src": media_url(p["storage_key"]), "alt": p["alt_text"]} for p in box["photos"]
    ]
    out.update({
        "id": str(box["id"]),
        "isActive": box["is_active"],
        "sortOrder": box["sort_order"],
        "createdAt": iso_utc(box["created_at"]),
        "updatedAt": iso_utc(box["updated_at"]),
        "tipoId": box["tipo_id"],
    })
    return out

def to_admin_detail(box: dict) -> dict:
    out = to_admin(box)
    out["contents"] = [{"product": product_to_public(i["product"]), "qty": i["qty"]} for i in box["items"]]
    return out

def tipo_to_admin(row: dict) -> dict:
    return {"id": row["id"], "nombre": row["nombre"]}

def availability(slug: str, missing: list[dict]) -> dict:
    return {"slug": slug, "soldOut": bool(missing), "available": not missing, "missing": missing}

# ---- Validación de entrada ------------------------------------------------------
def _parse_items(raw, errors: dict) -> list[dict] | None:
    if not isinstance(raw, list) or not raw:
        errors["items"] = "La caja necesita al menos un producto"
        return None
    items, seen = [], set()
    for it in raw:
        pid = parse_uuid(it.get("productId")) if isinstance(it, dict) else None
        qty = it.get("qty") if isinstance(it, dict) else None
        if not pid or not is_int(qty) or qty < 1 or pid in seen:
            errors["items"] = "Cada producto necesita un productId válido, sin repetir, y qty ≥ 1"
            return None
        seen.add(pid)
        items.append({"product_id": pid, "qty": qty})
    return items

def _parse(data: dict, required: bool) -> dict:
    errors, out = {}, {}
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
    if required or "tipoId" in data:
        tipo = data.get("tipoId")
        if not is_int(tipo):
            errors["tipoId"] = "Elige un tipo de caja válido"
        out["tipo_id"] = tipo
    for key, col in (("short", "short"), ("description", "description")):
        if key in data:
            if not isinstance(data[key], str):
                errors[key] = "Debe ser texto"
            out[col] = trim(data[key])
    if "emoji" in data:
        emoji = trim(data["emoji"])
        if not emoji or len(emoji) > 16:
            errors["emoji"] = "Escribe un emoji válido"
        out["emoji"] = emoji
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
    if required or "items" in data:
        items = _parse_items(data.get("items"), errors)
        if items is not None:
            out["items"] = items
    if errors:
        raise ValidationError(errors)
    return out

def parse_create(data: dict) -> dict:
    out = _parse(data, required=True)
    out.setdefault("emoji", "🎁")
    out.setdefault("short", "")
    out.setdefault("description", "")
    out.setdefault("is_active", True)
    out.setdefault("sort_order", 0)
    out.setdefault("image_ids", [])
    return out

def parse_update(data: dict) -> dict:
    return _parse(data, required=False)
