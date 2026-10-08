select
    snapshot_date,
    product_id,
    warehouse_id,
    qty_on_hand,
    qty_reserved,
    qty_available,
    lag(qty_on_hand) over (
        partition by product_id, warehouse_id
        order by snapshot_date
    )                                              as prev_qty_on_hand,
    qty_on_hand - lag(qty_on_hand) over (
        partition by product_id, warehouse_id
        order by snapshot_date
    )                                              as qty_change_day,
    case when qty_available <= 0 then true else false end as stockout_flag
from {{ ref('stg_inventory_snapshots') }}