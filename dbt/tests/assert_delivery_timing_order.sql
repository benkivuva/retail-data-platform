-- A delivery cannot be dispatched before the order was created,
-- and cannot be delivered before it was dispatched.
select
    d.delivery_id,
    d.order_id,
    o.order_timestamp,
    d.dispatch_at,
    d.delivered_at
from {{ ref('fct_deliveries') }} d
join {{ ref('fct_orders') }} o using (order_id)
where
    d.dispatch_at < o.order_timestamp
    or d.delivered_at < d.dispatch_at