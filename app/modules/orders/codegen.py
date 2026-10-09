"""Generación del `code` de reserva: 'PS-' + 6 caracteres [A-Z0-9]."""
import re
import secrets
import string
from collections.abc import Callable

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError

_ALPHABET = string.ascii_uppercase + string.digits
CODE_RE = re.compile(r"^PS-[A-Z0-9]{6}$")
MAX_ATTEMPTS = 5

def generate_code() -> str:
    return "PS-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))

def _constraint(err: IntegrityError) -> str | None:
    diag = getattr(getattr(err, "orig", None), "diag", None)
    return getattr(diag, "constraint_name", None)

def insert_with_unique_code(conn, insert_fn: Callable[[str], str]) -> tuple[str, str]:
    """Llama a `insert_fn(code)` hasta 5 veces si el code ya existe (UNIQUE).

    Cada intento va en un SAVEPOINT: un fallo UNIQUE no aborta la transacción del pedido.
    Devuelve (order_id, code).
    """
    for _ in range(MAX_ATTEMPTS):
        code = generate_code()
        try:
            with conn.begin_nested():
                return insert_fn(code), code
        except IntegrityError as err:
            if _constraint(err) != "orders_code_key":
                raise
    raise AppError("No se pudo generar el código de la reserva. Intenta de nuevo")
