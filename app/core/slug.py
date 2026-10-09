import re
import unicodedata

def slugify(text: str) -> str:
    """Idéntico al del frontend: NFD, sin diacríticos, minúsculas, no [a-z0-9] → '-'."""
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
