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


def _query(sql: str, params: list | None = None) -> pd.DataFrame:
    """Run a query and return a DataFrame, bypassing the Storage API."""
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    return _client().query(sql, job_config=job_config).to_dataframe(
        create_bqstorage_client=False
    )


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
            total_discount,
            total_delivery_fees,
            total_items,
            total_units,
            total_gross_margin,
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
    params = [bigquery.ScalarQueryParameter("days", "INT64", days)]
    return _query(sql, params)


@cache.memoize(timeout=300)
def get_customer_segments() -> pd.DataFrame:
    """Customer counts grouped by segment."""
    project = _client().project
    sql = f"""
        select
            segment,
            count(*) as customer_count
        from `{project}.marts.dim_customers`
        group by segment
        order by customer_count desc
    """
    return _query(sql)


@cache.memoize(timeout=300)
def get_customer_channels() -> pd.DataFrame:
    """Customer counts grouped by acquisition channel."""
    project = _client().project
    sql = f"""
        select
            acquisition_channel,
            count(*) as customer_count
        from `{project}.marts.dim_customers`
        group by acquisition_channel
        order by customer_count desc
    """
    return _query(sql)


@cache.memoize(timeout=300)
def get_customer_signups_by_month() -> pd.DataFrame:
    """Monthly signup counts, most recent 24 months."""
    project = _client().project
    sql = f"""
        select
            date_trunc(signup_date, month) as month,
            count(*)                       as signups
        from `{project}.marts.dim_customers`
        where signup_date >= date_sub(current_date(), interval 24 month)
        group by month
        order by month
    """
    return _query(sql)