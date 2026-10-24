"""Capa HTTP: un blueprint por recurso, separado en `public/` y `admin/`."""
import importlib

from flask import Flask

# El orden se conserva tal cual estaba registrado originalmente.
BLUEPRINT_MODULES = [
    "app.api.health",
    "app.api.admin.administradores",
    "app.api.admin.auth",
    "app.api.public.media",
    "app.api.admin.media",
    "app.api.admin.categorias",
    "app.api.public.products",
    "app.api.admin.products",
    "app.api.public.boxes",
    "app.api.admin.boxes",
    "app.api.admin.horas",
    "app.api.public.pickups",
    "app.api.admin.pickups",
    "app.api.public.orders",
    "app.api.admin.orders",
]


def register_blueprints(app: Flask) -> None:
    for name in BLUEPRINT_MODULES:
        app.register_blueprint(importlib.import_module(name).bp)
