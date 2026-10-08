select
    product_id,
    product_name,
    category,
    brand,
    unit_cost,
    unit_price,
    supplier_id,
    perishable_flag
from {{ source('raw', 'products') }}
