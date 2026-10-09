import os

def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default

class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://postgres:root@localhost:5432/prettystore")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-change-me")
    JWT_ACCESS_MINUTES = _int("JWT_ACCESS_MINUTES", 60)
    JWT_REFRESH_DAYS = _int("JWT_REFRESH_DAYS", 7)
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads")
    MEDIA_BASE_URL = os.environ.get("MEDIA_BASE_URL", "/media")
    MAX_UPLOAD_MB = _int("MAX_UPLOAD_MB", 5)
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
    MAX_CONTENT_LENGTH = _int("MAX_UPLOAD_MB", 5) * 1024 * 1024 + 1024 * 1024
    RATELIMIT_ENABLED = os.environ.get("RATELIMIT_ENABLED", "1") != "0"
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    JSON_AS_ASCII = False
