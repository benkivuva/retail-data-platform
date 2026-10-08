select
    p.payment_id,
    p.order_id,
    p.amount         as paid_amount,
    o.net_revenue    as order_net_revenue
from {{ ref('stg_payments') }} p
join {{ ref('stg_orders') }} o using (order_id)
where p.status = 'paid'
  and p.amount > o.net_revenue + 0.01