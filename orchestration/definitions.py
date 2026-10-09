"""Dagster definitions for the retail data platform.

Orchestrates the dbt project as a single asset graph, then runs Soda Core
checks on the raw layer for anomaly detection.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import dagster as dg
from dagster_dbt import (
    DbtCliResource,
    DbtProject,
    build_schedule_from_dbt_selection,
    dbt_assets,
)

ROOT_DIR = Path(__file__).parent.parent
DBT_PROJECT_DIR = ROOT_DIR / "dbt"
DBT_PROFILES_DIR = Path.home() / ".dbt"
SODA_CONFIG_PATH = ROOT_DIR / "soda" / "configuration.yml"
SODA_CHECKS_PATH = ROOT_DIR / "soda" / "checks.yml"

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROFILES_DIR,
)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def retail_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@dg.asset(
    deps=[retail_dbt_assets],
    compute_kind="soda",
    description="Soda Core scan for anomaly detection and raw data validation.",
    group_name="quality",
)
def soda_raw_checks(context):
    result = subprocess.run(
        [
            "uv", "run", "soda", "scan",
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


daily_pipeline = build_schedule_from_dbt_selection(
    [retail_dbt_assets],
    job_name="materialize_dbt_models",
    cron_schedule="0 6 * * *",
    dbt_select="fqn:*",
)


defs = dg.Definitions(
    assets=[retail_dbt_assets, soda_raw_checks],
    schedules=[daily_pipeline],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=DBT_PROFILES_DIR,
        ),
    },
)