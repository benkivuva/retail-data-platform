select
    supplier_order_id,
    supplier_id,
    product_id,
    ordered_qty,
    received_qty,
    ordered_at,
    received_at,
    date_diff(date(received_at), date(ordered_at), day)      as actual_lead_days,
    safe_divide(received_qty, nullif(ordered_qty, 0))        as fill_rate
from {{ ref('stg_supplier_orders') }}