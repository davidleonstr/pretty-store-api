from app.modules.media.routes_admin import bp as _admin_bp
from app.modules.media.routes_public import bp as _public_bp
from app.modules.media.service import ensure_exist

blueprints = [_public_bp, _admin_bp]

__all__ = ["blueprints", "ensure_exist"]
