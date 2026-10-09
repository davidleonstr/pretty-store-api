from app.modules.auth.decorators import admin_required  # noqa: I001  (primero: lo usan los routes_admin de otros módulos)
from app.modules.auth.routes_admin import bp as _admin_bp

blueprints = [_admin_bp]

__all__ = ["admin_required", "blueprints"]
