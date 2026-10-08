select distinct
    warehouse_id,
    warehouse_id as warehouse_name
from {{ ref('stg_orders') }}