"""Ask business questions against governed AI views.

The provider is chosen at runtime from the AI_PROVIDER environment
variable (default: gemini). Every provider shares the same system prompt
(ai/context.md) and the same SQL allowlist (ai/tools.py).

Two entry points:
  - ask(question) -> str    # used by the Flask platform
  - main()                  # CLI loop
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the repo root importable when this file is run directly as a script.
# Without this, `python ai/ask.py` cannot find the `ai` package.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.providers import get_provider  # noqa: E402

CONTEXT_PATH = Path(__file__).parent / "context.md"


def load_context() -> str:
    if CONTEXT_PATH.exists():
        return CONTEXT_PATH.read_text(encoding="utf-8")
    return (
        "You are a retail data analyst assistant. Answer business questions by "
        "running SELECT queries with the run_sql tool. Only query approved views."
    )


def ask(question: str) -> str:
    """Answer a single question. Used by the Flask platform's /ai/ask route."""
    provider = get_provider()
    return provider.ask(question, load_context())


def main() -> None:
    provider = get_provider()
    system_prompt = load_context()
    print(f"Ask a business question. Provider: {provider.name}. Type 'quit' to exit.")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if question.lower() in {"quit", "exit"}:
            return
        if not question:
            continue
        print()
        try:
            print(provider.ask(question, system_prompt))
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {exc}")


if __name__ == "__main__":
    main()