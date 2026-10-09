"""Pretty Store · application factory."""
import importlib
import os

from dotenv import load_dotenv
from flask import Flask

MODULES = [
    "administradores", "auth", "media", "categorias", "products",
    "boxes", "horas", "pickups", "clientes", "orders",
]


def create_app(overrides: dict | None = None) -> Flask:
    load_dotenv()
    from app.config import Config
    from app.core import db
    from app.core.errors import register_error_handlers
    from app.extensions import cors, jwt, limiter

    app = Flask(__name__)
    app.config.from_object(Config)
    app.json.ensure_ascii = False
    if overrides:
        app.config.update(overrides)

    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    db.init_engine(app.config["DATABASE_URL"])

    app.config["JWT_SECRET_KEY"] = app.config["JWT_SECRET_KEY"]
    from datetime import timedelta
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=app.config["JWT_ACCESS_MINUTES"])
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=app.config["JWT_REFRESH_DAYS"])
    app.config["JWT_ALGORITHM"] = "HS256"

    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    register_error_handlers(app)
    _register_jwt_errors(jwt)

    from app.health import bp as health_bp
    app.register_blueprint(health_bp)

    for name in MODULES:
        mod = importlib.import_module(f"app.modules.{name}")
        for bp in getattr(mod, "blueprints", []):
            app.register_blueprint(bp)

    from app.cli import register_cli
    register_cli(app)
    return app


def _register_jwt_errors(jwt):
    """Todos los fallos de JWT responden 401 con el formato de error global."""
    jwt.unauthorized_loader(lambda reason: _unauth())
    jwt.invalid_token_loader(lambda reason: _unauth())
    jwt.expired_token_loader(lambda header, data: _unauth())
    jwt.revoked_token_loader(lambda header, data: _unauth())
    jwt.needs_fresh_token_loader(lambda header, data: _unauth())


def _unauth():
    from flask import jsonify
    return jsonify({"error": {"code": "unauthorized", "message": "No autorizado"}}), 401
