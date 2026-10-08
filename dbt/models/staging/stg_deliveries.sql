select
    delivery_id,
    order_id,
    cast(dispatch_at as timestamp)   as dispatch_at,
    cast(delivered_at as timestamp)  as delivered_at,
    cast(promised_at as timestamp)   as promised_at,
    delivery_status,
    driver_id,
    zone_id
from {{ source('raw', 'deliveries') }}
