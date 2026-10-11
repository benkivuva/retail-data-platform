"""Gemini implementation of AIProvider.

Uses google-genai with manual function-calling. The model is restricted
to the run_sql tool, which enforces the SQL allowlist in ai.tools.
"""
from __future__ import annotations

import os

from google import genai
from google.genai import types

from ai.providers.base import AIProvider
from ai.tools import ALLOWED_TABLES, run_sql

MODEL = "gemini-3.8-flash"
MAX_TOOL_ITERATIONS = 10


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise SystemExit(
                "GEMINI_API_KEY not set. In PowerShell run:\n"
                '  $env:GEMINI_API_KEY = "your-key-here"'
            )
        self.client = genai.Client(api_key=key)

    def _tool(self) -> types.Tool:
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="run_sql",
                    description=(
                        "Run a BigQuery SQL SELECT against the ai dataset. "
                        "Allowed tables: " + ", ".join(sorted(ALLOWED_TABLES))
                    ),
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "sql": types.Schema(
                                type=types.Type.STRING,
                                description="BigQuery SQL SELECT statement.",
                            )
                        },
                        required=["sql"],
                    ),
                )
            ]
        )

    def ask(self, question: str, system_prompt: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[self._tool()],
        )

        contents = [
            types.Content(role="user", parts=[types.Part(text=question)])
        ]

        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )
            candidate = response.candidates[0]
            parts = candidate.content.parts

            calls = [p.function_call for p in parts if p.function_call]
            if not calls:
                text_parts = [p.text for p in parts if p.text]
                return "\n".join(text_parts).strip()

            contents.append(candidate.content)
            tool_parts = []
            for fc in calls:
                sql = fc.args.get("sql", "") if fc.args else ""
                result = run_sql(sql)
                tool_parts.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": result},
                    )
                )
            # Gemini expects tool responses in a user turn.
            contents.append(types.Content(role="user", parts=tool_parts))

        return "Stopped after 10 tool calls without a final answer."