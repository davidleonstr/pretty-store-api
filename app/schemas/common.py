from app.core.http import media_url


def photos_public(photos: list[dict], emoji: str) -> list[dict]:
    """Fotos públicas; si no hay ninguna, se usa el emoji como respaldo."""
    out = [{"src": media_url(p["storage_key"]), "alt": p["alt_text"]} for p in photos]
    return out or [{"emoji": emoji}]
