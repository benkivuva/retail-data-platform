-- Fails if any daily metric is out of its valid range.
select *
from {{ ref('metrics_daily') }}
where
    gmv < 0
    or net_revenue < 0
    or total_orders < 0
    or total_items < 0
    or (average_order_value is not null and average_order_value < 0)
    or (on_time_delivery_rate is not null and (on_time_delivery_rate < 0 or on_time_delivery_rate > 1))
    or (avg_delivery_minutes is not null and avg_delivery_minutes < 0)
    or stockout_products < 0