with order_items as (
    select
        order_id,
        count(*)                    as item_count,
        sum(quantity)               as total_quantity,
        sum(line_total)             as items_subtotal,
        sum(quantity * unit_cost)   as items_cost
    from {{ ref('stg_order_items') }}
    group by order_id
),

orders as (
    select *
    from {{ ref('stg_orders') }}
)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.order_timestamp,
    o.order_status,
    o.channel,
    o.delivery_zone_id,
    o.warehouse_id,
    o.gross_amount,
    o.discount_amount,
    o.delivery_fee,
    o.net_revenue,
    coalesce(i.item_count, 0)       as item_count,
    coalesce(i.total_quantity, 0)   as total_quantity,
    coalesce(i.items_subtotal, 0)   as items_subtotal,
    coalesce(i.items_cost, 0)       as items_cost,
    coalesce(i.items_subtotal, 0) - coalesce(i.items_cost, 0) as gross_margin
from orders o
left join order_items i using (order_id)