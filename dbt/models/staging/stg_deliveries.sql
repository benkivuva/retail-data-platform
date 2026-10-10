select
    delivery_id,
    order_id,
    cast(dispatch_at as timestamp)   as dispatch_at,
    cast(delivered_at as timestamp)  as delivered_at,
    cast(promised_at as timestamp)   as promised_at,
    delivery_status,
    driver_id,
    -- Source system uses ZN001-ZN006; ops sheet uses Z001-Z051.
    -- Reconcile to the sheet format so joins resolve.
    regexp_replace(zone_id, r'^ZN', 'Z') as zone_id
from {{ source('raw', 'deliveries') }}