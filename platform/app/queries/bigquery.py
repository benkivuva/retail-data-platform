"""BigQuery access layer.

All SQL lives here so dashboards never construct queries directly.
"""
from __future__ import annotations

import os
from functools import lru_cache

import pandas as pd
from google.cloud import bigquery

from ..extensions import cache


@lru_cache(maxsize=1)
def _client() -> bigquery.Client:
    """Return a singleton BigQuery client, configured from GCP_PROJECT."""
    project = os.getenv("GCP_PROJECT")
    if not project:
        raise RuntimeError("GCP_PROJECT environment variable is not set")
    return bigquery.Client(project=project)


@cache.memoize(timeout=300)
def get_daily_metrics(days: int = 90) -> pd.DataFrame:
    """Return daily business metrics for the last `days` days."""
    project = _client().project
    sql = f"""
        select
            metric_date,
            total_orders,
            gmv,
            net_revenue,
            average_order_value,
            deliveries_delivered,
            deliveries_on_time,
            on_time_delivery_rate,
            avg_delivery_minutes,
            stockout_products
        from `{project}.marts.metrics_daily`
        where metric_date >= date_sub(current_date(), interval @days day)
        order by metric_date
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("days", "INT64", days)]
    )
    # create_bqstorage_client=False uses the REST API instead of the
    # BigQuery Storage API, which needs a separate IAM permission
    # (bigquery.readsessions.create) that our service account doesn't have.
    return _client().query(sql, job_config=job_config).to_dataframe(
        create_bqstorage_client=False
    )