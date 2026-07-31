import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cafeteria-la-curva-cambiar-en-produccion")
    _database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cafeteria_la_curva.db'}")
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
