"""Pretty Store · application factory."""
import os
from datetime import timedelta

from flask import Flask

from app.api import register_blueprints
from app.cli import register_cli
from app.config import Config
from app.core.errors import register_error_handlers, register_jwt_errors
from app.db import session
from app.dependencies import cors, jwt, limiter


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json.ensure_ascii = False
    if overrides:
        app.config.update(overrides)

    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    session.init_engine(app.config["DATABASE_URL"])

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=app.config["JWT_ACCESS_MINUTES"])
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=app.config["JWT_REFRESH_DAYS"])
    app.config["JWT_ALGORITHM"] = "HS256"

    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config["CORS_ORIGINS"]}})
    register_error_handlers(app)
    register_jwt_errors(jwt)
    register_blueprints(app)
    register_cli(app)
    return app
