from app.constants import MIN_PASSWORD, MSG_PASSWORD
from app.core.errors import ValidationError
from app.core.validation import trim


def parse_login(data: dict) -> tuple[str, str]:
    """Devuelve (correo, password)."""
    return trim(data.get("correo")), data.get("password") or ""

def parse_change_password(data: dict) -> tuple[str, str]:
    """Devuelve (contraseña actual, contraseña nueva)."""
    nueva = data.get("nueva")
    if not isinstance(nueva, str) or len(nueva) < MIN_PASSWORD:
        raise ValidationError({"nueva": MSG_PASSWORD})
    return data.get("actual") or "", nueva
