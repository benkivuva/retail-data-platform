"""Dagster definitions for the retail data platform.

Three asset groups:
  - ingestion:  load ops Google Sheets into BigQuery raw
  - dbt:        one asset per dbt model (via dagster-dbt)
  - quality:    Soda Core scan on the raw layer

A daily schedule triggers the full pipeline at 06:00 Africa/Nairobi.

Subprocess calls use the venv's own interpreter and binaries (via
sys.executable) rather than `uv run`, so the container does not need uv
installed at runtime.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import dagster as dg
from dagster_dbt import (
    DbtCliResource,
    DbtProject,
    build_schedule_from_dbt_selection,
    dbt_assets,
)

# ------------------------------------------------------------------ paths
ROOT_DIR = Path(__file__).parent.parent
DBT_PROJECT_DIR = ROOT_DIR / "dbt"

# Prefer a container-provided profile directory; fall back to the repo's dbt/.
DBT_PROFILES_DIR = Path(
    os.getenv("DBT_PROFILES_DIR", str(ROOT_DIR / "dbt"))
)

SODA_CONFIG_PATH = ROOT_DIR / "soda" / "configuration.yml"
SODA_CHECKS_PATH = ROOT_DIR / "soda" / "checks.yml"

# Venv binaries, resolved from the interpreter running Dagster.
PYTHON_BIN = sys.executable
SODA_BIN = str(Path(sys.executable).parent / "soda")

# ------------------------------------------------------------------ dbt
dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROFILES_DIR,
)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def retail_dbt_assets(context, dbt: DbtCliResource):
    """One Dagster asset per dbt resource; runs `dbt build` (models + tests)."""
    yield from dbt.cli(["build"], context=context).stream()


# ------------------------------------------------------------------ ingestion
@dg.asset(
    compute_kind="python",
    description="Load ops Google Sheets into BigQuery raw layer.",
    group_name="ingestion",
)
def ops_sheets_ingestion(context) -> None:
    result = subprocess.run(
        [PYTHON_BIN, "data/scripts/load_sheets_to_bigquery.py"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise dg.Failure(description="Ops sheets load failed")


# ------------------------------------------------------------------ quality
@dg.asset(
    deps=[retail_dbt_assets],
    compute_kind="soda",
    description="Soda Core scan for anomaly detection and raw data validation.",
    group_name="quality",
)
def soda_raw_checks(context) -> None:
    result = subprocess.run(
        [
            SODA_BIN, "scan",
            "-d", "retail_bigquery",
            "-c", str(SODA_CONFIG_PATH),
            str(SODA_CHECKS_PATH),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise dg.Failure(
            description=f"Soda scan failed with exit code {result.returncode}",
        )


# ------------------------------------------------------------------ schedule
daily_pipeline = build_schedule_from_dbt_selection(
    [retail_dbt_assets],
    job_name="materialize_dbt_models",
    cron_schedule="0 6 * * *",
    execution_timezone="Africa/Nairobi",
    dbt_select="fqn:*",
)


# ------------------------------------------------------------------ defs
defs = dg.Definitions(
    assets=[
        retail_dbt_assets,
        ops_sheets_ingestion,
        soda_raw_checks,
    ],
    schedules=[daily_pipeline],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=DBT_PROFILES_DIR,
        ),
    },
)
