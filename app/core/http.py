from flask import current_app, jsonify, request

from app.core.errors import BadRequest, NotFound
from app.core.validation import parse_uuid


def media_url(storage_key: str) -> str:
    """URL pública de una imagen subida: <MEDIA_BASE_URL>/<storage_key>."""
    base = current_app.config["MEDIA_BASE_URL"].rstrip("/")
    return f"{base}/{storage_key}"

def uuid_or_404(value: str, message: str = "No encontrado") -> str:
    """Normaliza un uuid de la URL; 404 si no es válido."""
    uid = parse_uuid(value)
    if not uid:
        raise NotFound(message)
    return uid

def json_body(required: bool = True) -> dict:
    """Lee el JSON de la petición; 400 si es inválido o no es un objeto."""
    data = request.get_json(silent=True)
    if data is None:
        if required:
            raise BadRequest()
        return {}
    if not isinstance(data, dict):
        raise BadRequest()
    return data

def ok(data, status: int = 200):
    return jsonify(data), status

def created(data):
    return jsonify(data), 201

def no_content():
    return "", 204

      
