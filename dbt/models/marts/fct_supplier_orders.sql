select
    supplier_order_id,
    supplier_id,
    product_id,
    ordered_qty,
    received_qty,
    ordered_at,
    received_at,
    actual_lead_days,
    fill_rate
from {{ ref('int_supplier_lead_times') }}