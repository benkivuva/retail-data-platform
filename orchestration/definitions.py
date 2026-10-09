"""Dagster definitions for the retail data platform.

Orchestrates the dbt project as a single asset graph: one Dagster asset per
dbt model, with a daily schedule and a resource that invokes the dbt CLI.
"""
from pathlib import Path

import dagster as dg
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets, build_schedule_from_dbt_selection

# dbt project lives one level up from this file (orchestration/ -> project root)
DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt"

# dbt profiles live in the global dbt config directory (~/.dbt on Windows).
DBT_PROFILES_DIR = Path.home() / ".dbt"

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
    profiles_dir=DBT_PROFILES_DIR,
)
# Generate the manifest on first run in local/dev so Dagster can discover models.
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def retail_dbt_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    """One Dagster asset per dbt resource; runs `dbt build` (models + tests)."""
    yield from dbt.cli(["build"], context=context).stream()


daily_dbt_schedule = build_schedule_from_dbt_selection(
    [retail_dbt_assets],
    job_name="materialize_dbt_models",
    cron_schedule="0 6 * * *",          # 06:00 daily — data ready before workday
    dbt_select="fqn:*",                  # every model, seed, snapshot, and test
)


defs = dg.Definitions(
    assets=[retail_dbt_assets],
    schedules=[daily_dbt_schedule],
    resources={
        "dbt": DbtCliResource(
            project_dir=dbt_project,
            profiles_dir=DBT_PROFILES_DIR,
        ),
    },
)