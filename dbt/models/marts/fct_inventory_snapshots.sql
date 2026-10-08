select
    snapshot_date,
    product_id,
    warehouse_id,
    qty_on_hand,
    qty_reserved,
    qty_available,
    prev_qty_on_hand,
    qty_change_day,
    stockout_flag
from {{ ref('int_inventory_movements') }}