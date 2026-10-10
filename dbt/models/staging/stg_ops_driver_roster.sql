with cleaned as (
    select
        case
            when regexp_contains(trim(date), r'^\d{4}-\d{2}-\d{2}') then safe_cast(substr(date, 1, 10) as date)
            when regexp_contains(trim(date), r'^\d{2}/\d{2}/\d{4}$') then safe.parse_date('%d/%m/%Y', trim(date))
            when regexp_contains(trim(date), r'^[A-Za-z]+ \d{1,2}$') then safe.parse_date('%b %d 2026', trim(date))
            else null
        end                                             as roster_date,
        lower(trim(driver_name))                        as driver_name_raw,
        trim(phone)                                     as phone_raw,
        upper(trim(zone))                               as zone_raw,
        case
            when lower(trim(status)) = 'active' then 'active'
            when lower(trim(status)) = 'on leave' then 'on_leave'
            when lower(trim(status)) = 'sick' then 'sick'
            when trim(status) = '' then 'unknown'
            else lower(trim(status))
        end                                             as status
    from {{ source('raw', 'ops_driver_roster') }}
),

phone_normalised as (
    select
        *,
        case
            when regexp_contains(phone_raw, r'^\+2540') then null
            when regexp_contains(regexp_replace(phone_raw, r'[^0-9]', ''), r'^254\d{9}$')
                then concat('+', regexp_replace(phone_raw, r'[^0-9]', ''))
            when regexp_contains(regexp_replace(phone_raw, r'[^0-9]', ''), r'^0\d{9}$')
                then concat('+254', substr(regexp_replace(phone_raw, r'[^0-9]', ''), 2))
            when regexp_contains(regexp_replace(phone_raw, r'[^0-9]', ''), r'^[17]\d{8}$')
                then concat('+254', regexp_replace(phone_raw, r'[^0-9]', ''))
            else null
        end                                             as phone_e164
    from cleaned
)

select
    roster_date,
    driver_name_raw,
    phone_e164,
    zone_raw,
    status,
    case
        when z.zone_id is null then true
        else false
    end                                                 as zone_unknown_flag
from phone_normalised p
left join {{ ref('stg_ops_zone_master') }} z
    on upper(trim(p.zone_raw)) = upper(z.zone_name)
where driver_name_raw is not null
  and driver_name_raw != ''