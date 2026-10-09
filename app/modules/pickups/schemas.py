from datetime import date

from app.core.errors import ValidationError
from app.core.slug import slugify
from app.core.timeutil import hhmm, iso_utc, slot_label
from app.core.validation import is_int, trim

def _num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)

# ---- Serialización ----------------------------------------------------------
def hour_public(slot: dict) -> dict:
    return {
        "id": str(slot["slot_id"]),
        "label": slot_label(slot["fecha"], slot["hora"]),
        "fecha": slot["fecha"].isoformat(),
        "dia": slot["dia"],
        "hora": hhmm(slot["hora"]),
    }

def to_public(pickup: dict) -> dict:
    return {
        "id": pickup["id"],
        "name": pickup["name"],
        "address": pickup["address"],
        "lat": pickup["lat"],
        "lon": pickup["lon"],
        "hours": [hour_public(s) for s in pickup["slots"]],
    }

def to_admin(pickup: dict) -> dict:
    return {
        "id": pickup["id"],
        "name": pickup["name"],
        "address": pickup["address"],
        "lat": pickup["lat"],
        "lon": pickup["lon"],
        "isActive": pickup["is_active"],
        "sortOrder": pickup["sort_order"],
        "createdAt": iso_utc(pickup["created_at"]),
        "updatedAt": iso_utc(pickup["updated_at"]),
        "fechas": [fecha_to_admin(f) for f in pickup.get("fechas", [])],
    }

def fecha_to_admin(f: dict) -> dict:
    return {
        "id": str(f["id"]),
        "fecha": f["fecha"].isoformat(),
        "diaId": f["dia_id"],
        "dia": f["dia"],
        "isActive": f["is_active"],
        "sortOrder": f["sort_order"],
        "horas": [slot_to_admin(s) for s in f.get("slots", [])],
    }

def slot_to_admin(s: dict) -> dict:
    return {"id": str(s["slot_id"]), "horaId": s["hora_id"], "hora": hhmm(s["hora"]), "isActive": s["is_active"]}

def sin_horarios_to_admin(row: dict) -> dict:
    return {"id": row["id"], "name": row["name"]}

# ---- Validación -----------------------------------------------------------------
def _parse_pickup(data: dict, required: bool) -> dict:
    errors, out = {}, {}
    for key in ("name", "address"):
        if required or key in data:
            v = trim(data.get(key))
            if not v:
                errors[key] = "Este campo es obligatorio"
            out[key] = v
    if required or "lat" in data:
        lat = data.get("lat")
        if not _num(lat) or not -90 <= lat <= 90:
            errors["lat"] = "La latitud debe estar entre -90 y 90"
        out["lat"] = lat
    if required or "lon" in data:
        lon = data.get("lon")
        if not _num(lon) or not -180 <= lon <= 180:
            errors["lon"] = "La longitud debe estar entre -180 y 180"
        out["lon"] = lon
    if "isActive" in data:
        if not isinstance(data["isActive"], bool):
            errors["isActive"] = "Valor inválido"
        out["is_active"] = data["isActive"]
    if "sortOrder" in data:
        if not is_int(data["sortOrder"]):
            errors["sortOrder"] = "Debe ser un número entero"
        out["sort_order"] = data["sortOrder"]
    if errors:
        raise ValidationError(errors)
    return out

def parse_pickup_create(data: dict) -> dict:
    out = _parse_pickup(data, True)
    out["id"] = slugify(out["name"])
    if not out["id"]:
        raise ValidationError({"name": "Escribe un nombre válido"})
    out.setdefault("is_active", True)
    out.setdefault("sort_order", 0)
    return out

def parse_pickup_update(data: dict) -> dict:
    return _parse_pickup(data, False)

def parse_fecha_value(value) -> date:
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({"fecha": "Escribe una fecha válida con formato AAAA-MM-DD"})

def parse_fecha_create(data: dict) -> dict:
    out = {"fecha": parse_fecha_value(data.get("fecha"))}
    errors = {}
    hora_ids = data.get("horaIds", [])
    if not isinstance(hora_ids, list):
        errors["horaIds"] = "Debe ser una lista de horas"
    out["hora_ids"] = hora_ids
    out["is_active"] = data.get("isActive", True)
    out["sort_order"] = data.get("sortOrder", 0)
    if not isinstance(out["is_active"], bool):
        errors["isActive"] = "Valor inválido"
    if not is_int(out["sort_order"]):
        errors["sortOrder"] = "Debe ser un número entero"
    if errors:
        raise ValidationError(errors)
    return out

def parse_fecha_update(data: dict) -> dict:
    errors, out = {}, {}
    if "fecha" in data:
        out["fecha"] = parse_fecha_value(data["fecha"])
    if "isActive" in data:
        if not isinstance(data["isActive"], bool):
            errors["isActive"] = "Valor inválido"
        out["is_active"] = data["isActive"]
    if "sortOrder" in data:
        if not is_int(data["sortOrder"]):
            errors["sortOrder"] = "Debe ser un número entero"
        out["sort_order"] = data["sortOrder"]
    if errors:
        raise ValidationError(errors)
    return out

def parse_slot_create(data: dict) -> int:
    hora_id = data.get("horaId")
    if not is_int(hora_id):
        raise ValidationError({"horaId": "Elige una hora válida"})
    return hora_id

def parse_slot_update(data: dict) -> bool:
    if not isinstance(data.get("isActive"), bool):
        raise ValidationError({"isActive": "Debe ser true o false"})
    return data["isActive"]
