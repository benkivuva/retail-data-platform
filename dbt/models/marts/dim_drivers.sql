select distinct
    driver_id,
    driver_id as driver_name
from {{ ref('stg_deliveries') }}