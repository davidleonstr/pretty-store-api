from flask import current_app, jsonify, request

from app.core.errors import BadRequest

def media_url(storage_key: str) -> str:
    """URL pública de una imagen subida: <MEDIA_BASE_URL>/<storage_key>."""
    base = current_app.config["MEDIA_BASE_URL"].rstrip("/")
    return f"{base}/{storage_key}"

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
