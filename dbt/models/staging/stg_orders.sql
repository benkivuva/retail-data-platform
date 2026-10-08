select
    order_id,
    customer_id,
    cast(order_date as date)                as order_date,
    cast(order_timestamp as timestamp)      as order_timestamp,
    order_status,
    channel,
    delivery_zone_id,
    warehouse_id,
    cast(gross_amount as numeric)           as gross_amount,
    cast(discount_amount as numeric)        as discount_amount,
    cast(delivery_fee as numeric)           as delivery_fee,
    cast(net_revenue as numeric)            as net_revenue
from {{ source('raw', 'orders') }}
