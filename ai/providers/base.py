"""Abstract interface every AI provider implements.

The provider is responsible for:
  - loading its own API key
  - sending the system prompt, tools, and messages to the model
  - executing tool calls through ai.tools.run_sql
  - returning the final natural-language answer

The SQL allowlist in ai.tools is the only security boundary. Providers
must not bypass it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for AI providers."""

    name: str = "base"

    @abstractmethod
    def ask(self, question: str, system_prompt: str) -> str:
        """Send a question to the model and return the answer.

        Args:
            question: the user's natural-language question.
            system_prompt: the contents of ai/context.md.

        Returns:
            The model's final answer as plain text.
        """
        raise NotImplementedError