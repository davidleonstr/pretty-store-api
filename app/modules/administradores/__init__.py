from app.modules.administradores.routes_admin import bp as _admin_bp
from app.modules.administradores.service import get_active, get_by_correo, record_login, set_password

blueprints = [_admin_bp]

__all__ = ["blueprints", "get_active", "get_by_correo", "record_login", "set_password"]
