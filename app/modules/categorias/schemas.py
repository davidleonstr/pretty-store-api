from app.core.errors import ValidationError
from app.core.validation import is_int, trim

def to_admin(row: dict) -> dict:
    out = {"id": str(row["id"]), "nombre": row["nombre"], "sortOrder": row["sort_order"]}
    if "product_count" in row:
        out["productCount"] = row["product_count"]
    return out

def parse_create(data: dict) -> dict:
    errors = {}
    nombre = trim(data.get("nombre"))
    sort_order = data.get("sortOrder", 0)
    if not nombre or len(nombre) > 60:
        errors["nombre"] = "Escribe un nombre de hasta 60 caracteres"
    if not is_int(sort_order):
        errors["sortOrder"] = "Debe ser un número entero"
    if errors:
        raise ValidationError(errors)
    return {"nombre": nombre, "sort_order": sort_order}

def parse_update(data: dict) -> dict:
    errors, out = {}, {}
    if "nombre" in data:
        nombre = trim(data.get("nombre"))
        if not nombre or len(nombre) > 60:
            errors["nombre"] = "Escribe un nombre de hasta 60 caracteres"
        out["nombre"] = nombre
    if "sortOrder" in data:
        if not is_int(data["sortOrder"]):
            errors["sortOrder"] = "Debe ser un número entero"
        out["sort_order"] = data["sortOrder"]
    if errors:
        raise ValidationError(errors)
    return out
