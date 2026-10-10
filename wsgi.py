"""WSGI entry point for gunicorn.

Gunicorn runs: gunicorn wsgi:app
This file sets up sys.path so `import app` resolves to platform/app/.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
for p in (_ROOT, _ROOT / "platform"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app import create_app  # noqa: E402

app = create_app()