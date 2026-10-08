# Runbook

## Daily Rebuild

cd dbt
uv run dbt build

## Full Refresh (after schema changes)

cd dbt
uv run dbt build --full-refresh

## Regenerate Raw Data

Run from the repository root:

uv run python data/scripts/generate_raw_data.py
uv run python data/scripts/load_raw_to_bigquery.py
cd dbt
uv run dbt build --full-refresh

## Common Failures

### Test `assert_order_totals_match_items` fails

Orders and order items are out of sync. Check `raw.orders` and
`raw.order_items` for the affected `order_id`. If the source data is wrong,
fix the generator and reload.

### Test `assert_delivery_timing_order` fails

A delivery happened before its order or dispatch. Check clock synchronisation
in the source systems. If the generator is wrong, fix the seed logic.

### `metrics_daily.on_time_delivery_rate` is exactly 1.0 for many days

The denominator is being filtered too aggressively. Confirm
`fct_deliveries.delivery_status` includes both `delivered` and `delivered_late`.

### `bq load` fails on Windows with `FileNotFoundError`

The `bq` CLI is a `.cmd` wrapper on Windows. Confirm the loader script uses
`shell=True` on Windows. See `data/scripts/load_raw_to_bigquery.py`.

### BOM errors at the start of a SQL file

A file was written with a UTF-8 BOM. Rewrite it using the .NET method:

    [System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding $false))

Or install PowerShell 7 where `Set-Content -Encoding utf8` avoids BOM by default.

## On-Call Escalation

Analytics Engineering owns the pipeline end-to-end. Raise issues in the
`#data` channel.