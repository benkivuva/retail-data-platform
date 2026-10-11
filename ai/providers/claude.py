"""Claude implementation of AIProvider.

Uses the Anthropic SDK with tool use. Shares the same run_sql tool and
SQL allowlist as the Gemini provider. Requires ANTHROPIC_API_KEY to be
set and credits on the Anthropic account; the file is present regardless
so the layer is provider-agnostic by construction.
"""
from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic

from ai.providers.base import AIProvider
from ai.tools import ALLOWED_TABLES, run_sql

MODEL = "claude-sonnet-5-5"
MAX_TOOL_ITERATIONS = 10
KEY_PATH = Path(r"C:\keys\anthropic.txt")


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(self) -> None:
        key = None
        if KEY_PATH.exists():
            key = KEY_PATH.read_text().strip()
        key = key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise SystemExit(
                "Anthropic API key not found. Save it to C:\\keys\\anthropic.txt "
                "or set the ANTHROPIC_API_KEY environment variable."
            )
        self.client = Anthropic(api_key=key)

    def _tool(self) -> dict:
        return {
            "name": "run_sql",
            "description": (
                "Run a BigQuery SQL SELECT against the ai dataset. "
                "Allowed tables: " + ", ".join(sorted(ALLOWED_TABLES))
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "BigQuery SQL SELECT statement.",
                    }
                },
                "required": ["sql"],
            },
        }

    def ask(self, question: str, system_prompt: str) -> str:
        messages = [{"role": "user", "content": question}]

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=system_prompt,
                tools=[self._tool()],
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                parts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(parts).strip()

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                parts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(parts).strip()

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in tool_uses:
                sql = (block.input or {}).get("sql", "")
                output = run_sql(sql)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

        return "Stopped after 10 tool calls without a final answer."