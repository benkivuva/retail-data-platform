select
    supplier_id,
    supplier_name,
    lead_time_days,
    payment_terms,
    country
from {{ ref('stg_suppliers') }}