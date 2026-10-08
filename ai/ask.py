"""Ask business questions against governed AI views using Google Gemini.

Exposes the BigQuery `ai` dataset as a function tool. The model is restricted
to SELECT queries against approved views.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from google import genai
from google.genai import types
from google.cloud import bigquery

PROJECT_ID = "retail-data-platform-511008"
AI_DATASET = "ai"
MODEL = "gemini-3.8-flash"
ALLOWED_TABLES = {
    "ai_daily_metrics",
    "ai_customers_summary",
    "ai_products_summary",
}
CONTEXT_PATH = Path(__file__).parent / "context.md"


def load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "GEMINI_API_KEY not set. In PowerShell run:\n"
            '  $env:GEMINI_API_KEY = "your-key-here"'
        )
    return key


def load_context() -> str:
    if CONTEXT_PATH.exists():
        return CONTEXT_PATH.read_text(encoding="utf-8")
    return (
        "You are a retail data analyst assistant. Answer business questions by "
        "running SELECT queries with the run_sql tool. Only query these tables: "
        + ", ".join(sorted(ALLOWED_TABLES))
    )


def is_safe_query(sql: str) -> tuple[bool, str]:
    clean_sql = re.sub(r"\s+", " ", sql).strip().lower()

    if not clean_sql.startswith("select"):
        return False, "Only SELECT queries are allowed."

    if clean_sql.rstrip(";").count(";") > 0:
        return False, "Multiple SQL statements are not allowed."

    # Capture the full qualified table reference after FROM or JOIN,
    # including any project.dataset prefix and surrounding backticks.
    qualified = re.findall(r"(?:from|join)\s+([`\w.-]+)", clean_sql)

    if not qualified:
        return False, "Could not identify target tables in the query."

    found_tables = set()
    for name in qualified:
        cleaned = name.replace("`", "")
        # The table name is the last component of project.dataset.table.
        table = cleaned.rsplit(".", 1)[-1]
        found_tables.add(table)

    for table in found_tables:
        if table not in ALLOWED_TABLES:
            return False, f"Table '{table}' is not in the allowed views list."

    return True, ""


def run_sql(sql: str) -> str:
    """Run a BigQuery Standard SQL SELECT against permitted AI views.

    Args:
        sql: A strict SELECT statement targeting the ai dataset.
    """
    ok, err = is_safe_query(sql)
    if not ok:
        return f"Query rejected: {err}"

    try:
        client = bigquery.Client(project=PROJECT_ID)
        rows = list(client.query(sql).result(max_results=100))
        if not rows:
            return "Query returned no rows."
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        for row in rows:
            lines.append(" | ".join(str(row[h]) for h in headers))
        return "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        return f"BigQuery error: {exc}"


def ask(client: genai.Client, question: str) -> str:
    tool = types.Tool(
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

    config = types.GenerateContentConfig(
        system_instruction=load_context(),
        tools=[tool],
    )

    contents = [
        types.Content(role="user", parts=[types.Part(text=question)])
    ]

    for _ in range(10):
        response = client.models.generate_content(
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
        contents.append(types.Content(role="user", parts=tool_parts))

    return "Stopped after 10 tool calls without a final answer."


def main() -> None:
    client = genai.Client(api_key=load_api_key())
    print("Ask a business question. Type 'quit' to exit.")
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
            print(ask(client, question))
        except Exception as exc:  # noqa: BLE001
            print(f"[error] {exc}")


if __name__ == "__main__":
    main()