select
    cast(snapshot_date as date)      as snapshot_date,
    product_id,
    warehouse_id,
    cast(qty_on_hand as int64)       as qty_on_hand,
    cast(qty_reserved as int64)      as qty_reserved,
    cast(qty_available as int64)     as qty_available
from {{ source('raw', 'inventory_snapshots') }}
