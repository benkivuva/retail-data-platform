"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the platform/ folder regardless of CWD.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


class BaseConfig:
    """Configuration shared by all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    GCP_PROJECT: str = os.getenv("GCP_PROJECT", "")

    CACHE_TYPE: str = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT: int = 300


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False