"""Load raw CSVs into BigQuery's `raw` dataset using the `bq` CLI.

The target GCP project is read from the active gcloud configuration, so the
script works on any machine where `gcloud auth login` and
`gcloud config set project <id>` have been run.

Schema is autodetected from the CSV header. Each target table is fully
replaced on every run, making the load idempotent.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "raw"
DATASET = "raw"

TABLES = [
    "suppliers",
    "products",
    "customers",
    "orders",
    "order_items",
    "payments",
    "deliveries",
    "inventory_snapshots",
    "supplier_orders",
]

IS_WINDOWS = os.name == "nt"


def detect_project() -> str:
    """Return the active gcloud project, or exit with a helpful message."""
    result = subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        capture_output=True,
        text=True,
        shell=IS_WINDOWS,
    )
    project = result.stdout.strip()
    if result.returncode != 0 or not project or project == "(unset)":
        raise SystemExit(
            "No GCP project is set. Run:\n"
            "  gcloud auth login\n"
            "  gcloud config set project YOUR_PROJECT_ID"
        )
    return project


def find_bq() -> str:
    """Return the path to the `bq` executable, or exit with a helpful message."""
    path = shutil.which("bq")
    if not path:
        raise SystemExit(
            "The `bq` CLI was not found on PATH. Install it with:\n"
            "  gcloud components install bq"
        )
    return path


def load_table(bq: str, project_id: str, name: str) -> None:
    """Load a single CSV into BigQuery, replacing the target table."""
    csv_path = RAW_DIR / f"{name}.csv"
    if not csv_path.exists():
        print(f"  [skip] {csv_path.name} not found")
        return

    target = f"{project_id}:{DATASET}.{name}"
    flags = (
        "--source_format=CSV "
        "--skip_leading_rows=1 "
        "--autodetect "
        "--replace"
    )

    print(f"  loading {name} -> {target}")

    if IS_WINDOWS:
        # On Windows `bq` is a .cmd wrapper, so it must be invoked via the
        # shell. Quote every dynamic part to survive spaces in paths.
        cmd = f'"{bq}" load {flags} "{target}" "{csv_path}"'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        )
    else:
        # On POSIX we pass an argument list and avoid the shell entirely.
        args = [
            bq, "load",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            "--autodetect",
            "--replace",
            target,
            str(csv_path),
        ]
        result = subprocess.run(
            args, shell=False, capture_output=True, text=True
        )

    if result.returncode != 0:
        print(f"  [error] {name}")
        print(result.stderr.strip())
        sys.exit(1)

    print(f"  [ok] {name}")


def main() -> None:
    project_id = detect_project()
    bq = find_bq()
    print(f"Loading raw CSVs into {project_id}.{DATASET}\n")

    for name in TABLES:
        load_table(bq, project_id, name)

    print("\nAll tables loaded.")


if __name__ == "__main__":
    main()