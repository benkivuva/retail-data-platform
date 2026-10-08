select
    supplier_order_id,
    supplier_id,
    product_id,
    cast(ordered_qty as int64)       as ordered_qty,
    cast(received_qty as int64)      as received_qty,
    cast(ordered_at as timestamp)    as ordered_at,
    cast(received_at as timestamp)   as received_at
from {{ source('raw', 'supplier_orders') }}
