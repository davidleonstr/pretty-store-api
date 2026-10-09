import re
import uuid

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

def trim(value) -> str:
    return value.strip() if isinstance(value, str) else ""

def is_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value or ""))

def phone_digits(value) -> str:
    return re.sub(r"\D", "", value) if isinstance(value, str) else ""

def is_valid_phone(value) -> bool:
    return 8 <= len(phone_digits(value)) <= 15

def parse_uuid(value) -> str | None:
    """Devuelve el uuid normalizado o None si es inválido."""
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return None

def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)
