"""Categorías, productos y cajas iniciales.

IMPORTANTE: los archivos del frontend (src/data/products.js y src/data/boxes.js) no estaban
disponibles al generar este backend. Las listas de abajo son una MUESTRA de ejemplo con la
misma estructura; reemplázalas por los 24 productos y las 8 cajas reales (mismos slugs/precios).
El seed es idempotente: productos y cajas existentes (por slug) no se tocan.
"""
from app.core.db import execute

CATEGORIAS = ["Cuidado", "Dormir", "Aroma"]

def seed(conn) -> None:
    for i, nombre in enumerate(CATEGORIAS):
        execute(conn, "INSERT INTO categorias (nombre, sort_order) VALUES (:n, :s) ON CONFLICT (lower(nombre)) DO NOTHING",
                {"n": nombre, "s": i})
