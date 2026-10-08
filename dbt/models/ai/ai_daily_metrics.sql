{{ config(materialized='view', schema='ai') }}

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
from {{ ref('metrics_daily') }}