"""Thin wrapper around the governed AI assistant in ai/ask.py.

Keeps the Gemini client cached and exposes a single `answer()` function the
Flask routes call.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

from google import genai

# The ai/ package lives at the project root, not inside platform/.
# platform/app/ai/service.py -> parents[3] is the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Return a cached Gemini client, using GEMINI_API_KEY."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to platform/.env."
        )
    return genai.Client(api_key=key)


def answer(question: str) -> str:
    """Ask the governed assistant a business question and return its reply."""
    from ai.ask import ask

    return ask(_client(), question)