select
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    p.unit_cost,
    p.unit_price,
    p.perishable_flag,
    p.supplier_id,
    s.supplier_name
from {{ ref('stg_products') }} p
left join {{ ref('stg_suppliers') }} s using (supplier_id)