# Cost Report

This document records the cost-relevant decisions made in the platform and
where they can be improved. BigQuery charges on bytes scanned (queries) and
bytes stored. Both are addressed below.

## Design decisions that reduce cost

### 1. Layered materialisation

| Layer | Materialisation | Why |
|---|---|---|
| `staging` | View | No storage cost, always fresh |
| `intermediate` | View | No storage cost, reused by marts |
| `marts` | Table | Heavily queried; avoids rescanning joins |
| `ai` | View | Reads from marts; no extra storage |

Rationale: expensive joins and business logic run once into tables, then BI
and AI tools read the small materialised output instead of recomputing joins
on every query.

### 2. Column selection, not SELECT *

Every model selects only the columns it needs. `SELECT *` would scan every
column including ones later dropped downstream. This is especially important
in BigQuery, where cost is proportional to columns read, not rows.

### 3. Aggregation before serving

`metrics_daily` reduces millions of fact rows to one row per calendar day.
Dashboards and AI assistants query this instead of scanning `fct_orders`
or `fct_order_items`, cutting scanned bytes by orders of magnitude.

### 4. Date filtering expected in queries

`metrics_daily.metric_date` is the natural filter. Dashboards and the AI
context document both require date ranges, which prevents full-table scans.

## Cost-relevant tests

The metric `metrics_daily` is tested by `assert_metrics_daily_within_bounds`
and `unique_metrics_daily_metric_date`. If these fail, downstream BI and AI
queries are blocked by CI, preventing incorrect results from being queried
repeatedly while debugging.

## Improvements not yet implemented

| Improvement | Expected saving | Effort |
|---|---|---|
| Partition `fct_orders` and `fct_deliveries` by `order_date` | 60–80% on date-filtered scans | Low |
| Cluster `fct_order_items` by `product_id` | 40–60% on product joins | Low |
| Set table expiration on `raw` (e.g. 90 days) | Storage only | Low |
| Replace `int_inventory_movements` view with incremental table | 50%+ on daily rebuilds | Medium |
| Add `maximum_bytes_billed` to dbt profile | Hard cap on runaway queries | Low |
| Monitor via BigQuery INFORMATION_SCHEMA.JOBS daily | Visibility | Medium |

## How to measure

Bytes scanned per query:

    SELECT
      job_id,
      query,
      total_bytes_billed,
      total_bytes_processed
    FROM `region-us`.INFORMATION_SCHEMA.JOBS
    WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      AND job_type = 'QUERY'
    ORDER BY total_bytes_billed DESC
    LIMIT 20

## Ownership

Maintained by Analytics Engineering. Any change to materialisation, partitioning,
or a dashboard that increases scanned bytes should be documented here.