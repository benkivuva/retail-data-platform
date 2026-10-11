"""Governed SQL tool: allowlist and BigQuery execution.

Both the Gemini and Claude providers use these functions. The allowlist is
the single security boundary — no provider implementation bypasses it.
"""
from __future__ import annotations

import re

from google.cloud import bigquery

PROJECT_ID = "retail-data-platform-511008"
AI_DATASET = "ai"
ALLOWED_TABLES = {
    "ai_daily_metrics",
    "ai_customers_summary",
    "ai_products_summary",
}


def is_safe_query(sql: str) -> tuple[bool, str]:
    """Verify a query is a strict SELECT targeting only allowed views."""
    clean_sql = re.sub(r"\s+", " ", sql).strip().lower()

    if not clean_sql.startswith("select"):
        return False, "Only SELECT queries are allowed."

    if clean_sql.rstrip(";").count(";") > 0:
        return False, "Multiple SQL statements are not allowed."

    # Capture the full qualified table reference after FROM or JOIN.
    qualified = re.findall(r"(?:from|join)\s+([`\w.-]+)", clean_sql)

    if not qualified:
        return False, "Could not identify target tables in the query."

    found_tables = set()
    for name in qualified:
        cleaned = name.replace("`", "")
        # The table name is the last component of project.dataset.table.
        found_tables.add(cleaned.rsplit(".", 1)[-1])

    for table in found_tables:
        if table not in ALLOWED_TABLES:
            return False, f"Table '{table}' is not in the allowed views list."

    return True, ""


def run_sql(sql: str) -> str:
    """Run a BigQuery SELECT against the ai dataset, with allowlist enforcement.

    Returns a pipe-delimited string of results, or an error message.
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