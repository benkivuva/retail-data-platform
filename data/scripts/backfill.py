"""Backfill a dbt model (or selection) for a specific date range.

Wraps `dbt run` with `--vars` so models can filter on `start_date` and
`end_date`. Models that do not reference these vars are unaffected, so the
script degrades gracefully: it will run, but without date filtering.

Usage:
    uv run python data/scripts/backfill.py --model fct_orders --start 2026-09-01 --end 2026-09-30
    uv run python data/scripts/backfill.py --model +fct_orders --start 2026-09-01 --end 2026-09-30
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DBT_DIR = ROOT_DIR / "dbt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill a dbt model for a date range.",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="dbt model name or selection (e.g. fct_orders, +fct_orders, tag:daily).",
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY-MM-DD), inclusive.",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="End date (YYYY-MM-DD), inclusive.",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Add --full-refresh (drops and rebuilds; use with care on large models).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command without executing it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.start > args.end:
        raise SystemExit(f"start ({args.start}) must be <= end ({args.end})")

    vars_json = f'{{"start_date": "{args.start}", "end_date": "{args.end}"}}'

    cmd = [
        "uv", "run", "dbt", "run",
        "--select", args.model,
        "--vars", vars_json,
    ]
    if args.full_refresh:
        cmd.append("--full-refresh")

    pretty = " ".join(cmd)
    print(f"Backfill: {args.model}")
    print(f"Range:    {args.start} -> {args.end}")
    print(f"Command:  {pretty}\n")

    if args.dry_run:
        print("[dry-run] not executing.")
        return

    result = subprocess.run(cmd, cwd=DBT_DIR)
    if result.returncode != 0:
        print(f"\nBackfill failed with exit code {result.returncode}.")
        sys.exit(result.returncode)

    print("\nBackfill complete.")


if __name__ == "__main__":
    main()