from datetime import time

from app.core.db import execute, fetch_all, fetch_one

def list_all(conn) -> list[dict]:
    return fetch_all(conn, "SELECT id, hora FROM horas ORDER BY hora ASC")

def get_by_id(conn, hora_id: int) -> dict | None:
    return fetch_one(conn, "SELECT id, hora FROM horas WHERE id = :id", {"id": hora_id})

def exists_hora(conn, hora: time) -> bool:
    return fetch_one(conn, "SELECT 1 AS x FROM horas WHERE hora = :h", {"h": hora}) is not None

def count_existing(conn, hora_ids: list[int]) -> int:
    if not hora_ids:
        return 0
    return fetch_one(conn, "SELECT count(*) AS n FROM horas WHERE id = ANY(:ids)", {"ids": list(hora_ids)})["n"]

def insert(conn, hora: time) -> dict:
    return fetch_one(conn, "INSERT INTO horas (hora) VALUES (:h) RETURNING id, hora", {"h": hora})

def is_in_use(conn, hora_id: int) -> bool:
    """Lectura sobre pickup_fecha_horas (tabla de `pickups`) solo para validar el borrado."""
    return fetch_one(conn, "SELECT 1 AS x FROM pickup_fecha_horas WHERE hora_id = :id LIMIT 1", {"id": hora_id}) is not None

def delete(conn, hora_id: int) -> int:
    return execute(conn, "DELETE FROM horas WHERE id = :id", {"id": hora_id})
