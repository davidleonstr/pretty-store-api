import re
from datetime import time

from app.core.errors import ValidationError
from app.core.timeutil import hhmm

_HORA_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?$")

def to_admin(row: dict) -> dict:
    return {"id": row["id"], "hora": hhmm(row["hora"])}

def parse_create(data: dict) -> time:
    raw = data.get("hora")
    m = _HORA_RE.match(raw.strip()) if isinstance(raw, str) else None
    if not m:
        raise ValidationError({"hora": "Escribe una hora válida con formato HH:MM"})
    return time(int(m.group(1)), int(m.group(2)))
