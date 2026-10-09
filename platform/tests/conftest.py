"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# The platform/ folder must be on sys.path so `import app` resolves.
# (Naming the folder "platform" collides with Python's stdlib module.)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_PLATFORM_DIR = _PROJECT_ROOT / "platform"
for p in (_PROJECT_ROOT, _PLATFORM_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app import create_app  # noqa: E402
from app.config import BaseConfig  # noqa: E402
from app.extensions import db  # noqa: E402


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = "SimpleCache"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        from app.auth.models import User

        user = User(email="test@example.com", role="admin", display_name="Test")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()