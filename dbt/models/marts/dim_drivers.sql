-- One row per driver, with the most recent phone number on record.
-- driver_id is a deterministic surrogate key hashed from the normalised name.
with latest_phone as (
    select
        driver_name_raw,
        array_agg(phone_e164 ignore nulls order by roster_date desc limit 1)[offset(0)] as phone_e164
    from {{ ref('stg_ops_driver_roster') }}
    group by driver_name_raw
),

aggregated as (
    select
        d.driver_name_raw,
        p.phone_e164,
        count(*)                                            as roster_assignments,
        countif(d.status = 'active')                        as active_assignments,
        min(d.roster_date)                                  as first_assignment,
        max(d.roster_date)                                  as last_assignment
    from {{ ref('stg_ops_driver_roster') }} d
    left join latest_phone p using (driver_name_raw)
    group by d.driver_name_raw, p.phone_e164
)

select
    to_hex(md5(driver_name_raw))                        as driver_id,
    driver_name_raw                                     as driver_name,
    phone_e164,
    roster_assignments,
    active_assignments,
    first_assignment,
    last_assignment
from aggregated