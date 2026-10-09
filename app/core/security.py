from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_ph = PasswordHasher()  # argon2id por defecto
_DUMMY_HASH = _ph.hash("dummy-password-for-timing")

def hash_password(password: str) -> str:
    return _ph.hash(password)

def verify_password(password_hash: str | None, password: str) -> bool:
    """Verifica siempre un hash (aunque el usuario no exista) para igualar tiempos."""
    try:
        return _ph.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
