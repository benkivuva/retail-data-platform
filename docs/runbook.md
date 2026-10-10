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

## Reload the Ops Google Sheet

Run from the repository root:

uv run python data/scripts/load_sheets_to_bigquery.py

Then rebuild the models that depend on it:

cd dbt
uv run dbt build --select stg_ops_zone_master+ stg_ops_driver_roster+ stg_ops_vehicle_log+

The loader is idempotent — it uses `WRITE_TRUNCATE`, so each run replaces the
`raw.ops_*` tables with the current sheet contents.

## Orchestration

Run the full pipeline under Dagster (ingestion → dbt → Soda):

uv run dagster dev -f orchestration/definitions.py

Then open http://127.0.0.1:3000 and click **Materialize all** in the Assets
tab, or use the daily 6 AM schedule.

## Soda Checks

Standalone run:

uv run soda scan -d retail_bigquery -c soda/configuration.yml soda/checks.yml

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

### Sheet loader fails with `403 PERMISSION_DENIED`

The service account cannot see the sheet. Open the sheet in Google Sheets,
click **Share**, and confirm `dbt-runner@retail-data-platform-511008.iam.gserviceaccount.com`
is listed with **Viewer** access.

### Sheet loader fails with an empty error message

The Google Sheets API and Google Drive API are not enabled on the GCP project.
Enable both:

- https://console.cloud.google.com/apis/library/sheets.googleapis.com
- https://console.cloud.google.com/apis/library/drive.googleapis.com

Wait 1–2 minutes, then re-run.

### Test `unique_stg_ops_zone_master_zone_id` fails

The source Google Sheet contains duplicate `zone_id` values. Check the sheet
for two rows with the same zone ID. The staging model deduplicates them
automatically using `row_number()`, so a test failure means the dedup logic
did not run — verify the model was rebuilt:

cd dbt
uv run dbt run --select stg_ops_zone_master --full-refresh

If the test still fails after a rebuild, the same zone_id has a NULL value on
one of the rows. Fix the source sheet and reload.

### Duplicate rows appear in `dim_delivery_zones` or `dim_drivers`

The source sheet has duplicate entries that were not deduplicated. Check the
count query:

SELECT zone_id, COUNT(*) FROM `retail-data-platform-511008.staging.stg_ops_zone_master` GROUP BY zone_id HAVING COUNT(*) > 1

If rows are returned, report the duplicates to the Operations team (the sheet
owner) so they can fix the source. The staging model's dedup will handle it on
the next run once the sheet is corrected.

### `Unrecognized name: driver_id` in a marts test

The `dim_drivers` model uses a surrogate key (`driver_id` derived from the
hashed name), but a test is referencing a column that doesn't exist. Confirm
`_marts.yml` includes a `driver_id` entry with `unique` and `not_null` tests,
and that `dim_drivers.sql` produces that column.

### BOM errors at the start of a SQL file

A file was written with a UTF-8 BOM. Rewrite it using the .NET method:

    [System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding $false))

Or install PowerShell 7 where `Set-Content -Encoding utf8` avoids BOM by default.

### `Illegal escape sequence: \_` in a BigQuery query

BigQuery does not accept backslash-escaped underscores. Remove the backslash
or use a raw string:

    WHERE upper(trim(zone_id)) NOT LIKE 'ZONE_ID%'
    -- or --
    WHERE upper(trim(zone_id)) NOT LIKE r'ZONE_ID%'

### DML queries are not allowed in the free tier

BigQuery Sandbox blocks `MERGE`, `INSERT`, `UPDATE`, and `DELETE`. Incremental
dbt models and dbt snapshots require DML, so they cannot run on the free tier.
The `fct_orders` model keeps its incremental configuration commented out with
a note on how to enable it once billing is set up.

To activate incremental materialization:

1. Link a billing account to the GCP project.
2. In `dbt/models/marts/fct_orders.sql`, change `materialized='table'` to
   `materialized='incremental'` and uncomment `unique_key` and
   `on_schema_change`.
3. Uncomment the `{% if is_incremental() %}` block at the bottom.
4. Run `uv run dbt run --select fct_orders --full-refresh` once, then
   normal `dbt run` afterwards.

## On-Call Escalation

Analytics Engineering owns the pipeline end-to-end. Raise issues in the
`#data` channel.

For issues with the source Google Sheet itself (wrong data, missing zones,
duplicate rows), contact the Operations team owner directly. The pipeline
handles defensively what it can, but source-side corrections need to happen
in the sheet.