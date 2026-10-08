select distinct
    zone_id,
    zone_id as zone_name
from {{ ref('stg_deliveries') }}