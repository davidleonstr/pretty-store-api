from app.modules.boxes.routes_admin import bp as _admin_bp
from app.modules.boxes.routes_public import bp as _public_bp
from app.modules.boxes.service import get_by_slugs, get_requirements

blueprints = [_public_bp, _admin_bp]

__all__ = ["blueprints", "get_by_slugs", "get_requirements"]
