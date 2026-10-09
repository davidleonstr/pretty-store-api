from app.modules.orders.routes_admin import bp as _admin_bp
from app.modules.orders.routes_public import bp as _public_bp

blueprints = [_public_bp, _admin_bp]  # ningún otro módulo usa `orders`

__all__ = ["blueprints"]
