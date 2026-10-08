"""Ask business questions against governed AI views.

Uses Claude with the BigQuery `ai` dataset exposed as a tool. The model
is only allowed to run SELECT queries against approved views defined in
context.md.
"""
from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic
from google.cloud import bigquery

PROJECT_ID = "retail-data-platform-511008"
AI_DATASET = "ai"
ALLOWED_TABLES = {
    "ai_daily_metrics",
    "ai_customers_summary",
    "ai_products_summary",
}
CONTEXT_PATH = Path(__file__).parent / "context.md"
KEY_PATH = Path(r"C:\keys\anthropic.txt")


def load_api_key() -> str:
    if KEY_PATH.exists():
        return KEY_PATH.read_text().strip()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit(
            "Anthropic API key not found. Save it to C:\\keys\\anthropic.txt "
            "or set the ANTHROPIC_API_KEY environment variable."
        )
    return key


def load_context() -> str:
    return CONTEXT_PATH.read_text(encoding="utf-8")


def is_safe_query(sql: str) -> tuple[bool, str]:
    lower = sql.lower().strip()
    if not lower.startswith("select"):
        return False, "Only SELECT queries are allowed."
    for forbidden in ("insert", "update", "delete", "drop", "create", "alter"):
        if f" {forbidden} " in f" {lower} ":
            return False, f"Keyword '{forbidden}' is not allowed."
    if f"`{PROJECT_ID}.{AI_DATASET}." not in sql and f"{AI_DATASET}." not in sql:
        return False, "Queries must target the ai dataset only."
    return True, ""


def run_bigquery(sql: str) -> str:
    client = bigquery.Client(project=PROJECT_ID)
    rows = list(client.query(sql).result(max_results=100))
    if not rows:
        return "No rows returned."
    headers = list(rows[0].keys())
    lines = [" | ".join(headers)]
    for row in rows:
        lines.append(" | ".join(str(row[h]) for h in headers))
    return "\n".join(lines)


TOOLS = [
    {
        "name": "run_sql",
        "description": (
            "Run a BigQuery Standard SQL SELECT query against the ai dataset. "
            "Only tables ai_daily_metrics, ai_customers_summary, and "
            "ai_products_summary are permitted."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "BigQuery SQL SELECT query."}
            },
            "required": ["sql"],
        },
    }
]


def handle_tool_call(name: str, tool_input: dict) -> str:
    if name != "run_sql":
        return f"Unknown tool: {name}"
    sql = tool_input.get("sql", "")
    ok, err = is_safe_query(sql)
    if not ok:
        return f"Query rejected: {err}"
    try:
        return run_bigquery(sql)
    except Exception as exc:  # noqa: BLE001
        return f"BigQuery error: {exc}"


def ask(question: str) -> str:
    client = Anthropic(api_key=load_api_key())
    system = load_context()
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            tools=TOOLS,
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
            output = handle_tool_call(block.name, block.input)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": output,
            })
        messages.append({"role": "user", "content": tool_results})


def main() -> None:
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
        print(ask(question))


if __name__ == "__main__":
    main()