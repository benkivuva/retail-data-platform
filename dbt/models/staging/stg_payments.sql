select
    payment_id,
    order_id,
    method,
    cast(amount as numeric)          as amount,
    status,
    cast(paid_at as timestamp)       as paid_at
from {{ source('raw', 'payments') }}
