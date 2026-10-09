from app.modules.products.routes_admin import bp as _admin_bp
from app.modules.products.routes_public import bp as _public_bp
from app.modules.products.service import deduct_stock, get_by_ids, get_by_slugs, get_stock_map, restore_stock

blueprints = [_public_bp, _admin_bp]

__all__ = ["blueprints", "get_by_slugs", "get_by_ids", "get_stock_map", "deduct_stock", "restore_stock"]
