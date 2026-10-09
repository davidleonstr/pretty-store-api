"""Horas, puntos de retiro y, para cada punto, fechas y slots de las próximas 4 semanas.
"""
from datetime import time as dtime

def _t(hhmm: str) -> dtime:
    h, m = hhmm.split(":")
    return dtime(int(h), int(m))

def seed(conn) -> None:
    pass