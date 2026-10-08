select
    order_item_id,
    order_id,
    product_id,
    cast(quantity as int64)          as quantity,
    cast(unit_price as numeric)      as unit_price,
    cast(unit_cost as numeric)       as unit_cost,
    cast(line_total as numeric)      as line_total
from {{ source('raw', 'order_items') }}
