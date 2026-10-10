with cleaned as (
    select
        upper(regexp_replace(trim(vehicle_reg), r'[^A-Za-z0-9]', '')) as vehicle_reg,
        trim(description)                                            as description_raw,
        case
            when regexp_contains(trim(last_service), r'^\d{4}-\d{2}-\d{2}') then safe_cast(substr(last_service, 1, 10) as date)
            when regexp_contains(trim(last_service), r'^\d{2}/\d{2}/\d{4}$') then safe.parse_date('%d/%m/%Y', trim(last_service))
            when regexp_contains(trim(last_service), r'^\d{2}-\d{2}-\d{2}$') then safe.parse_date('%d-%m-%y', trim(last_service))
            when regexp_contains(trim(last_service), r'^[A-Za-z]+ \d{1,2}$') then safe.parse_date('%b %d 2026', trim(last_service))
            else null
        end                                                          as last_service_date,
        case
            when trim(cost) = '' then null
            when regexp_contains(upper(trim(cost)), r'K$')
                then safe_cast(regexp_replace(upper(cost), r'[^0-9.]', '') as numeric) * 1000
            else safe_cast(regexp_replace(cost, r'[^0-9.]', '') as numeric)
        end                                                          as cost_kes,
        nullif(trim(remarks), '')                                     as remarks
    from {{ source('raw', 'ops_vehicle_log') }}
)

select
    vehicle_reg,
    case
        when lower(description_raw) like '%hiace%' then 'Toyota Hiace'
        when lower(description_raw) like '%npr%'   then 'Isuzu NPR'
        when lower(description_raw) like '%canter%' then 'Mitsubishi Canter'
        when lower(description_raw) like '%nv200%' then 'Nissan NV200'
        when lower(description_raw) like '%probox%' then 'Toyota Probox'
        when lower(description_raw) like '%carry%' then 'Suzuki Carry'
        else 'Unknown'
    end                                                              as vehicle_type,
    description_raw,
    last_service_date,
    cost_kes,
    remarks
from cleaned
where vehicle_reg is not null
  and vehicle_reg != ''
  and vehicle_reg not like 'VEHICLE%'