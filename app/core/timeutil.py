from datetime import date, datetime, time
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/El_Salvador")

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

def now_sv() -> datetime:
    return datetime.now(TZ)

def slot_datetime(fecha: date, hora: time) -> datetime:
    return datetime.combine(fecha, hora.replace(tzinfo=None), tzinfo=TZ)

def is_future(fecha: date, hora: time) -> bool:
    return slot_datetime(fecha, hora) > now_sv()

def hora_label(hora: time) -> str:
    h12 = hora.hour % 12 or 12
    suf = "AM" if hora.hour < 12 else "PM"
    return f"{h12}:{hora.minute:02d} {suf}"

def slot_label(fecha: date, hora: time) -> str:
    dia = DIAS[fecha.isoweekday() - 1]
    return f"{dia} {fecha.day} de {MESES[fecha.month - 1]} · {hora_label(hora)}"

def hhmm(hora: time) -> str:
    return f"{hora.hour:02d}:{hora.minute:02d}"

def iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")
