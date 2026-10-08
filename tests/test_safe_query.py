"""Unit tests for the SQL allowlist in ai/ask.py."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai"))

from ask import ALLOWED_TABLES, is_safe_query  # noqa: E402


def test_accepts_plain_select():
    sql = "SELECT metric_date, gmv FROM ai.ai_daily_metrics"
    ok, err = is_safe_query(sql)
    assert ok, err


def test_accepts_fully_qualified_table():
    sql = (
        "SELECT * FROM `retail-data-platform-511008.ai.ai_daily_metrics` "
        "WHERE metric_date >= '2026-01-01'"
    )
    ok, err = is_safe_query(sql)
    assert ok, err


def test_accepts_every_allowlisted_table():
    for table in ALLOWED_TABLES:
        sql = f"SELECT * FROM ai.{table}"
        ok, err = is_safe_query(sql)
        assert ok, f"Failed for {table}: {err}"


def test_rejects_non_select():
    for sql in (
        "DELETE FROM ai.ai_daily_metrics",
        "UPDATE ai.ai_daily_metrics SET gmv = 0",
        "DROP TABLE ai.ai_daily_metrics",
    ):
        ok, err = is_safe_query(sql)
        assert not ok, f"Should reject: {sql}"
        assert "SELECT" in err


def test_rejects_multiple_statements():
    sql = "SELECT * FROM ai.ai_daily_metrics; DROP TABLE ai.ai_daily_metrics"
    ok, _ = is_safe_query(sql)
    assert not ok


def test_rejects_non_allowlisted_table():
    for sql in (
        "SELECT * FROM raw.orders",
        "SELECT * FROM marts.fct_orders",
        "SELECT * FROM ai.customers",
    ):
        ok, err = is_safe_query(sql)
        assert not ok, f"Should reject: {sql}"
        assert "not in the allowed" in err


def test_rejects_query_without_tables():
    ok, _ = is_safe_query("SELECT 1")
    assert not ok