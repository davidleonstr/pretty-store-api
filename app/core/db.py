"""Acceso a PostgreSQL con SQLAlchemy Core (SQL explícito, sin ORM)."""
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Engine | None = None

def init_engine(database_url: str) -> Engine:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = create_engine(database_url, pool_pre_ping=True, future=True)
    return _engine

def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("El motor de BD no está inicializado")
    return _engine

@contextmanager
def connection():
    """Conexión de solo lectura (sin transacción explícita de escritura)."""
    with get_engine().connect() as conn:
        yield conn
        conn.rollback()

@contextmanager
def transaction():
    """Abre una transacción; confirma al salir o revierte ante una excepción."""
    with get_engine().begin() as conn:
        yield conn

def fetch_all(conn, sql: str, params: dict | None = None) -> list[dict]:
    return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]

def fetch_one(conn, sql: str, params: dict | None = None) -> dict | None:
    row = conn.execute(text(sql), params or {}).mappings().first()
    return dict(row) if row else None

def execute(conn, sql: str, params: dict | None = None) -> int:
    return conn.execute(text(sql), params or {}).rowcount
