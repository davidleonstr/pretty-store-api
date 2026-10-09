from app.modules.pickups.routes_admin import bp as _admin_bp
from app.modules.pickups.routes_public import bp as _public_bp
from app.modules.pickups.service import describe_slot, get_available_slot

blueprints = [_public_bp, _admin_bp]

__all__ = ["blueprints", "get_available_slot", "describe_slot"]
