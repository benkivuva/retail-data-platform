select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    o.order_date,
    o.order_status,
    o.channel,
    o.customer_id,
    oi.quantity,
    oi.unit_price,
    oi.unit_cost,
    oi.line_total,
    oi.quantity * oi.unit_cost       as line_cost,
    oi.line_total - (oi.quantity * oi.unit_cost) as line_margin
from {{ ref('stg_order_items') }} oi
left join {{ ref('stg_orders') }} o using (order_id)