select
    delivery_id,
    order_id,
    dispatch_at,
    delivered_at,
    promised_at,
    delivery_status,
    driver_id,
    zone_id,
    delivery_minutes,
    minutes_vs_promise,
    on_time_flag
from {{ ref('int_delivery_times') }}