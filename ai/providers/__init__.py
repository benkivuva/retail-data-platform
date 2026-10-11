"""AI provider factory. Selects an implementation from the AI_PROVIDER env var."""
from __future__ import annotations

import os

from ai.providers.base import AIProvider


def get_provider() -> AIProvider:
    """Return the configured provider. Defaults to Gemini."""
    name = os.environ.get("AI_PROVIDER", "gemini").strip().lower()
    if name == "gemini":
        from ai.providers.gemini import GeminiProvider
        return GeminiProvider()
    if name == "claude":
        from ai.providers.claude import ClaudeProvider
        return ClaudeProvider()
    raise SystemExit(
        f"Unknown AI_PROVIDER '{name}'. Supported: gemini, claude."
    )