from app.core.errors import ValidationError
from app.core.timeutil import iso_utc
from app.core.validation import is_email, trim

MIN_PASSWORD = 10
MSG_PASSWORD = f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres"

def to_admin(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "nombre": row["nombre"],
        "correo": row["correo"],
        "activo": row["activo"],
        "ultimoLoginAt": iso_utc(row.get("ultimo_login_at")),
        "createdAt": iso_utc(row.get("created_at")),
        "updatedAt": iso_utc(row.get("updated_at")),
    }

def to_me(row: dict) -> dict:
    return {"id": str(row["id"]), "nombre": row["nombre"], "correo": row["correo"]}

def parse_create(data: dict) -> dict:
    errors = {}
    nombre = trim(data.get("nombre"))
    correo = trim(data.get("correo")).lower()
    password = data.get("password")
    if not nombre or len(nombre) > 120:
        errors["nombre"] = "Escribe un nombre válido"
    if not is_email(correo):
        errors["correo"] = "Escribe un correo válido"
    if not isinstance(password, str) or len(password) < MIN_PASSWORD:
        errors["password"] = MSG_PASSWORD
    if errors:
        raise ValidationError(errors)
    return {"nombre": nombre, "correo": correo, "password": password}

def parse_update(data: dict) -> dict:
    errors, out = {}, {}
    if "nombre" in data:
        nombre = trim(data.get("nombre"))
        if not nombre or len(nombre) > 120:
            errors["nombre"] = "Escribe un nombre válido"
        out["nombre"] = nombre
    if "activo" in data:
        if not isinstance(data["activo"], bool):
            errors["activo"] = "Valor inválido"
        out["activo"] = data["activo"]
    if "password" in data:
        if not isinstance(data["password"], str) or len(data["password"]) < MIN_PASSWORD:
            errors["password"] = MSG_PASSWORD
        out["password"] = data["password"]
    if errors:
        raise ValidationError(errors)
    return out
