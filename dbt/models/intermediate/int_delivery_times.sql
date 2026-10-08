select
    delivery_id,
    order_id,
    dispatch_at,
    delivered_at,
    promised_at,
    delivery_status,
    driver_id,
    zone_id,
    timestamp_diff(delivered_at, dispatch_at, minute)   as delivery_minutes,
    timestamp_diff(delivered_at, promised_at, minute)   as minutes_vs_promise,
    case
        when delivered_at <= promised_at then true
        else false
    end                                                 as on_time_flag
from {{ ref('stg_deliveries') }}