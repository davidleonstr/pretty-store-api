"""Errores de dominio y manejador global (formato de la sección 3)."""
from flask import jsonify
from werkzeug.exceptions import HTTPException

class AppError(Exception):
    status = 500
    code = "internal_error"
    message = "Error interno"

    def __init__(self, message: str | None = None, **extra):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.extra = extra

    def to_dict(self) -> dict:
        body = {"code": self.code, "message": self.message}
        body.update(self.extra)
        return {"error": body}

class BadRequest(AppError):
    status = 400
    code = "bad_request"
    message = "JSON inválido"

class ValidationError(AppError):
    status = 422
    code = "validation_error"
    message = "Datos inválidos"

    def __init__(self, fields: dict | None = None, message: str | None = None):
        super().__init__(message, fields=fields or {})
        self.fields = fields or {}

class NotFound(AppError):
    status = 404
    code = "not_found"
    message = "No encontrado"

class Conflict(AppError):
    status = 409
    code = "conflict"
    message = "Conflicto"

    def __init__(self, code: str = "conflict", message: str | None = None, **extra):
        super().__init__(message or self.message, **extra)
        self.code = code

class Unauthorized(AppError):
    status = 401
    code = "unauthorized"
    message = "No autorizado"

class Forbidden(AppError):
    status = 403
    code = "forbidden"
    message = "Acceso denegado"

class PayloadTooLarge(AppError):
    status = 413
    code = "payload_too_large"
    message = "El archivo es demasiado grande"

class UnsupportedMediaType(AppError):
    status = 415
    code = "unsupported_media_type"
    message = "Tipo de archivo no permitido"

class TooManyRequests(AppError):
    status = 429
    code = "too_many_requests"
    message = "Demasiadas solicitudes. Intenta más tarde"

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _app_error(err: AppError):
        return jsonify(err.to_dict()), err.status

    @app.errorhandler(HTTPException)
    def _http_error(err: HTTPException):
        mapping = {
            400: BadRequest, 401: Unauthorized, 403: Forbidden, 404: NotFound,
            413: PayloadTooLarge, 415: UnsupportedMediaType, 429: TooManyRequests,
        }
        cls = mapping.get(err.code or 500)
        if cls:
            return jsonify(cls().to_dict()), cls.status
        body = {"error": {"code": "http_error", "message": err.description or "Error"}}
        return jsonify(body), err.code or 500

    @app.errorhandler(Exception)
    def _unexpected(err: Exception):
        app.logger.exception("Error no controlado")
        return jsonify(AppError().to_dict()), 500
