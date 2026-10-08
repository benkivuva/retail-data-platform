select *
from {{ ref('fct_supplier_orders') }}
where received_qty > ordered_qty