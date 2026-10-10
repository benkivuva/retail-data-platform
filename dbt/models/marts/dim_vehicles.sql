-- One row per vehicle, with the most recent maintenance record.
with latest_service as (
    select
        vehicle_reg,
        array_agg(last_service_date ignore nulls order by last_service_date desc limit 1)[offset(0)] as last_service_date,
        array_agg(cost_kes ignore nulls order by last_service_date desc limit 1)[offset(0)] as last_service_cost_kes
    from {{ ref('stg_ops_vehicle_log') }}
    group by vehicle_reg
)

select
    v.vehicle_reg,
    max(v.vehicle_type)                                 as vehicle_type,
    count(*)                                            as service_count,
    min(v.last_service_date)                            as first_service_date,
    max(v.last_service_date)                            as last_service_date,
    s.last_service_cost_kes,
    sum(v.cost_kes)                                     as total_cost_kes
from {{ ref('stg_ops_vehicle_log') }} v
left join latest_service s using (vehicle_reg)
group by v.vehicle_reg, s.last_service_cost_kes