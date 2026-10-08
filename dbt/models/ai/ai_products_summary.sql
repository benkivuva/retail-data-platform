{{ config(materialized='view', schema='ai') }}

select
    category,
    count(*)                    as product_count,
    avg(unit_price)             as avg_price,
    avg(unit_cost)              as avg_cost,
    avg(unit_price - unit_cost) as avg_margin
from {{ ref('dim_products') }}
group by category