from app.modules.horas.routes_admin import bp as _admin_bp
from app.modules.horas.service import ensure_exist

blueprints = [_admin_bp]

__all__ = ["blueprints", "ensure_exist"]
