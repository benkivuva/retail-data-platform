select *
from {{ ref('fct_inventory_snapshots') }}
where qty_on_hand < 0
   or qty_reserved < 0
   or qty_available < 0