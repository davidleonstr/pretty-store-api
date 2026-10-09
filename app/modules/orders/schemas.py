from datetime import date, datetime, time, timedelta

from app.core.errors import ValidationError
from app.core.timeutil import TZ, hhmm, iso_utc, slot_label
from app.core.validation import is_email, is_int, is_valid_phone, parse_uuid, trim

STATUSES = ("pendiente", "en proceso", "por entregar", "entregado", "cancelado")
KINDS = ("caja", "productos")

MSG = {
    "nombres": "Escribe tus nombres",
    "apellidos": "Escribe tus apellidos",
    "celular": "Escribe un número de celular válido",
    "correo": "Escribe un correo válido",
    "pickupId": "Elige un lugar de entrega",
    "horaId": "Elige una hora disponible",
    "nota": "La nota no puede pasar de 300 caracteres",
    "items": "Revisa los productos de tu pedido",
}

# ---- Serialización ----------------------------------------------------------
def _customer(o: dict) -> dict:
    return {"nombres": o["nombres"], "apellidos": o["apellidos"], "celular": o["celular"], "correo": o["correo"]}

def _pickup(o: dict) -> dict:
    return {
        "id": o["pickup_id"],
        "name": o["pickup_name"],
        "address": o["pickup_address"],
        "horaId": str(o["pickup_fecha_hora_id"]),
        "fecha": o["fecha_retiro"].isoformat(),
        "dia": o["dia"],
        "hora": hhmm(o["hora"]),
        "label": slot_label(o["fecha_retiro"], o["hora"]),
    }

def _items(items: list[dict]) -> list[dict]:
    return [{"name": i["name"], "unitPriceCents": i["unit_price_cents"], "qty": i["qty"]} for i in items]

def created(order_id: str, code: str, total_cents: int) -> dict:
    return {"id": order_id, "code": code, "status": "pendiente", "totalCents": total_cents}

def to_customer_detail(o: dict, items: list[dict]) -> dict:
    return {
        "id": str(o["id"]),
        "code": o["code"],
        "kind": o["kind"],
        "status": o["status"],
        "customer": _customer(o),
        "nota": o["nota"],
        "pickup": _pickup(o),
        "items": _items(items),
        "totalCents": o["total_cents"],
        "canModify": o["status"] == "pendiente",
        "createdAt": iso_utc(o["created_at"]),
    }

def to_admin_detail(o: dict, items: list[dict]) -> dict:
    return {
        "id": str(o["id"]),
        "code": o["code"],
        "kind": o["kind"],
        "status": o["status"],
        "customer": _customer(o),
        "nota": o["nota"],
        "pickup": _pickup(o),
        "items": _items(items),
        "totalCents": o["total_cents"],
        "deliveredAt": iso_utc(o["delivered_at"]),
        "createdAt": iso_utc(o["created_at"]),
        "updatedAt": iso_utc(o["updated_at"]),
    }

def to_admin_summary(o: dict) -> dict:
    return {
        "id": str(o["id"]),
        "code": o["code"],
        "kind": o["kind"],
        "status": o["status"],
        "customer": _customer(o),
        "pickup": _pickup(o),
        "totalCents": o["total_cents"],
        "deliveredAt": iso_utc(o["delivered_at"]),
        "createdAt": iso_utc(o["created_at"]),
    }

# ---- Validación de entrada ------------------------------------------------------
def _check_customer(raw, errors: dict, partial: bool) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    out = {}
    rules = {
        "nombres": lambda v: bool(v),
        "apellidos": lambda v: bool(v),
        "celular": lambda v: is_valid_phone(v),
        "correo": lambda v: is_email(v),
    }
    for key, valid in rules.items():
        if partial and key not in raw:
            continue
        value = trim(raw.get(key))
        if not valid(value):
            errors[key] = MSG[key]
        out[key] = value
    return out

def _check_nota(data: dict, errors: dict, out: dict, partial: bool) -> None:
    if partial and "nota" not in data:
        return
    nota = data.get("nota", "")
    if nota is None:
        nota = ""
    if not isinstance(nota, str) or len(nota.strip()) > 300:
        errors["nota"] = MSG["nota"]
    else:
        out["nota"] = nota.strip()

def _check_retiro(data: dict, errors: dict, out: dict, partial: bool) -> None:
    if partial and "pickupId" not in data and "horaId" not in data:
        return
    pickup_id = trim(data.get("pickupId"))
    hora_id = parse_uuid(data.get("horaId")) if isinstance(data.get("horaId"), str) else None
    if not pickup_id:
        errors["pickupId"] = MSG["pickupId"]
    if not hora_id:
        errors["horaId"] = MSG["horaId"]
    out["pickup_id"] = pickup_id
    out["hora_id"] = hora_id

def parse_create(data: dict) -> dict:
    errors, out = {}, {}
    kind = data.get("kind")
    if kind not in KINDS:
        errors["kind"] = "Elige una caja o productos"
    out["kind"] = kind

    raw_items = data.get("items")
    items = []
    if isinstance(raw_items, list) and raw_items:
        for it in raw_items:
            slug = trim(it.get("slug")) if isinstance(it, dict) else ""
            qty = it.get("qty") if isinstance(it, dict) else None
            if not slug or not is_int(qty) or qty < 1:
                items = []
                break
            items.append({"slug": slug, "qty": qty})
    if not items:
        errors["items"] = MSG["items"]
    out["items"] = items

    out["customer"] = _check_customer(data.get("customer"), errors, partial=False)
    _check_retiro(data, errors, out, partial=False)
    _check_nota(data, errors, out, partial=False)
    out.setdefault("nota", "")
    if errors:
        raise ValidationError(errors)
    return out

def parse_update(data: dict) -> dict:
    errors, out = {}, {}
    if "customer" in data:
        if not isinstance(data["customer"], dict):
            errors["customer"] = "Datos del cliente inválidos"
        else:
            out["customer"] = _check_customer(data["customer"], errors, partial=True)
    if ("pickupId" in data) != ("horaId" in data):
        errors["horaId" if "pickupId" in data else "pickupId"] = "Envía pickupId y horaId juntos"
    else:
        _check_retiro(data, errors, out, partial=True)
    _check_nota(data, errors, out, partial=True)
    if errors:
        raise ValidationError(errors)
    return out

def parse_status(data: dict) -> str:
    status = data.get("status")
    if status not in STATUSES:
        raise ValidationError({"status": f"Debe ser uno de: {', '.join(STATUSES)}"})
    return status

def parse_admin_filters(args) -> dict:
    errors = {}
    status, kind = args.get("status") or None, args.get("kind") or None
    if status and status not in STATUSES:
        errors["status"] = f"Debe ser uno de: {', '.join(STATUSES)}"
    if kind and kind not in KINDS:
        errors["kind"] = "Debe ser caja o productos"

    def _date(name):
        raw = args.get(name)
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            errors[name] = "Escribe una fecha válida con formato AAAA-MM-DD"
            return None

    d_from, d_to = _date("from"), _date("to")
    if errors:
        raise ValidationError(errors)
    # from/to son fechas locales (El Salvador); `to` es inclusiva.
    ts_from = datetime.combine(d_from, time.min, tzinfo=TZ) if d_from else None
    ts_to = datetime.combine(d_to + timedelta(days=1), time.min, tzinfo=TZ) if d_to else None
    return {"status": status, "kind": kind, "q": trim(args.get("q")) or None, "ts_from": ts_from, "ts_to": ts_to}
