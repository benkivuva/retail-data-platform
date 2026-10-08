-- Order items_subtotal must reconcile with the sum of line_total
-- from fct_order_items for the same order.
with item_totals as (
    select
        order_id,
        sum(line_total) as summed_line_total
    from {{ ref('fct_order_items') }}
    group by order_id
)

select
    o.order_id,
    o.items_subtotal,
    i.summed_line_total
from {{ ref('fct_orders') }} o
join item_totals i using (order_id)
where abs(o.items_subtotal - i.summed_line_total) > 0.01