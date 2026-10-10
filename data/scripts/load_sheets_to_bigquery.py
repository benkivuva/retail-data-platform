"""Load ops tracker Google Sheets into BigQuery raw layer.

Reads a shared Google Sheet using the dbt-runner service account. Loads
each tab as-is into raw.ops_* tables with all columns typed as STRING.
Does not clean, validate, or cast — that is dbt staging's job.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

PROJECT_ID = "retail-data-platform-511008"
SA_KEY_PATH = r"C:\keys\retail-data-platform-sa-v2.json"
SHEET_ID = "1Nv3Pm2UyzHSJncSN_JM3s1tOumy9hWJQfDzyf931MeM"

# header_row_index is 0-based. Zone Master has a title row and a blank row
# before the real header. The other two start at row 1.
TABS = {
    "Zone Master": {"header_row_index": 2, "table": "ops_zone_master"},
    "Driver Roster": {"header_row_index": 0, "table": "ops_driver_roster"},
    "Vehicle Log": {"header_row_index": 0, "table": "ops_vehicle_log"},
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/cloud-platform",
]


def sanitize_headers(headers: list[str]) -> list[str]:
    """Turn messy sheet headers into BigQuery-safe column names."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for h in headers:
        base = re.sub(r"[^a-z0-9_]", "_", h.strip().lower()).strip("_") or "col"
        if base in seen:
            seen[base] += 1
            base = f"{base}_{seen[base]}"
        else:
            seen[base] = 1
        out.append(base)
    return out


def get_clients():
    creds = Credentials.from_service_account_file(SA_KEY_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    bq = bigquery.Client(project=PROJECT_ID, credentials=creds)
    return gc, bq


def load_tab(gc, bq, tab_name: str, config: dict) -> None:
    print(f"  reading tab: {tab_name}")
    sheet = gc.open_by_key(SHEET_ID)
    ws = sheet.worksheet(tab_name)
    rows = ws.get_all_values()

    header_idx = config["header_row_index"]
    if len(rows) <= header_idx:
        print(f"  [skip] {tab_name}: not enough rows")
        return

    raw_headers = rows[header_idx]
    headers = sanitize_headers(raw_headers)
    data_rows = rows[header_idx + 1:]

    records = []
    for row in data_rows:
        # Skip fully blank rows (the section breaks in Zone Master).
        if not any(cell.strip() for cell in row):
            continue
        # Pad short rows to header length.
        row = row + [""] * (len(headers) - len(row))
        records.append({headers[i]: row[i] for i in range(len(headers))})

    if not records:
        print(f"  [skip] {tab_name}: no data rows")
        return

    schema = [bigquery.SchemaField(h, "STRING") for h in headers]
    table_id = f"{PROJECT_ID}.raw.{config['table']}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
    )

    print(f"  loading {len(records)} rows into {table_id}")
    bq.load_table_from_json(records, table_id, job_config=job_config).result()
    print(f"  [ok] {tab_name} -> {table_id}")


def main() -> None:
    print(f"Loading ops sheets from {SHEET_ID}\n")
    gc, bq = get_clients()
    for tab_name, config in TABS.items():
        try:
            load_tab(gc, bq, tab_name, config)
        except Exception as exc:  # noqa: BLE001
            print(f"  [error] {tab_name}: {type(exc).__name__}")
            print(f"  {repr(exc)}")
            if hasattr(exc, "response"):
                print(f"  response: {exc.response.text}")
            sys.exit(1)
    print("\nAll ops tabs loaded.")


if __name__ == "__main__":
    main()