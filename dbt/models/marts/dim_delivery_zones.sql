select
    z.zone_id,
    z.zone_name,
    z.county,
    z.dispatch_hub,
    z.is_active
from {{ ref('stg_ops_zone_master') }} z