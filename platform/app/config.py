"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)

_DB_PATH = Path(__file__).resolve().parent.parent / "platform.db"
_DEFAULT_DB_URL = f"sqlite:///{_DB_PATH.as_posix()}"


class BaseConfig:
    """Configuration shared by all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    GCP_PROJECT: str = os.getenv("GCP_PROJECT", "")

    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    CACHE_TYPE: str = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT: int = 300

    # Session cookie hardening
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = False   # overridden to True in ProdConfig
    PERMANENT_SESSION_LIFETIME: int = 8 * 60 * 60   # 8 hours

    WTF_CSRF_ENABLED: bool = True


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True           # HTTPS only in prod
    PREFERRED_URL_SCHEME = "https"