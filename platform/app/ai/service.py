"""Thin wrapper around the governed AI assistant in ai/ask.py.

The assistant is provider-agnostic (see ai/providers/). This wrapper simply
imports the public ask() function and exposes it to the Flask routes.
"""
from __future__ import annotations

import sys
from pathlib import Path

# The ai/ package lives at the project root, not inside platform/.
# platform/app/ai/service.py -> parents[3] is the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def answer(question: str) -> str:
    """Ask the governed assistant a business question and return its reply."""
    from ai.ask import ask

    return ask(question)