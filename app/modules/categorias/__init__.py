from app.modules.categorias.routes_admin import bp as _admin_bp
from app.modules.categorias.service import ensure_exists

blueprints = [_admin_bp]

__all__ = ["blueprints", "ensure_exists"]
