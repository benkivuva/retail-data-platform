"""Tests for the AI SQL allowlist — the safety layer around Gemini."""
from __future__ import annotations

from ai.ask import is_safe_query


def test_select_against_allowed_table_passes():
    ok, _ = is_safe_query("SELECT * FROM ai_daily_metrics")
    assert ok is True


def test_qualified_select_passes():
    ok, _ = is_safe_query(
        "SELECT category FROM `retail-data-platform-511008.ai.ai_products_summary`"
    )
    assert ok is True


def test_non_select_is_rejected():
    ok, err = is_safe_query("DROP TABLE ai_daily_metrics")
    assert ok is False
    assert "SELECT" in err


def test_multi_statement_is_rejected():
    ok, err = is_safe_query("SELECT 1; DROP TABLE ai_daily_metrics")
    assert ok is False


def test_disallowed_table_is_rejected():
    ok, err = is_safe_query("SELECT * FROM raw.orders")
    assert ok is False
    assert "orders" in err


def test_staging_table_is_rejected():
    ok, _ = is_safe_query("SELECT * FROM stg_orders")
    assert ok is False


def test_marts_table_is_rejected():
    ok, _ = is_safe_query("SELECT * FROM marts.metrics_daily")
    assert ok is False