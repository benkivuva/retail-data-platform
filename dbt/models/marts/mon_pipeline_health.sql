{{ config(materialized='table', schema='marts') }}

-- One row per run. Captures current pipeline health: freshness, row counts,
-- and the lag between today and the latest metric_date. Overwrites each run.
select
    current_timestamp()                                         as checked_at,
    (select max(metric_date) from {{ ref('metrics_daily') }})   as latest_metric_date,
    date_diff(
        current_date(),
        (select max(metric_date) from {{ ref('metrics_daily') }}),
        day
    )                                                           as metric_freshness_lag_days,
    (select count(*) from {{ ref('fct_orders') }})              as total_orders,
    (select count(*) from {{ ref('fct_deliveries') }})          as total_deliveries,
    (select count(*) from {{ ref('fct_inventory_snapshots') }}) as total_inventory_rows,
    (select count(*) from {{ ref('fct_order_items') }})         as total_order_items,
    (select max(order_date) from {{ ref('fct_orders') }})       as latest_order_date