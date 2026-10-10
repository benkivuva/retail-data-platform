with cleaned as (
    select
        trim(zone_id)                                       as zone_id,
        initcap(trim(zone_name))                            as zone_name,
        case
            when lower(trim(county)) in ('nairobi', 'nbo') then 'Nairobi'
            when lower(trim(county)) in ('kiambu', 'kbu', 'kia') then 'Kiambu'
            else initcap(trim(county))
        end                                                 as county,
        trim(dispatch_hub)                                  as dispatch_hub,
        case
            when upper(trim(active)) in ('Y', 'YES', 'TRUE', '1') then true
            when trim(active) = '' or active is null then null
            else false
        end                                                 as is_active
    from {{ source('raw', 'ops_zone_master') }}
    where zone_id is not null
      and trim(zone_id) != ''
      and upper(trim(zone_id)) not like 'ZONE_ID%'
),

-- Source has duplicate zone_id values with different spellings (e.g. Z028
-- appears as Kileleshwa and Kileleswa). Keep one row per zone_id: the one
-- with the most non-null fields, tie-broken by alphabetical name.
deduped as (
    select
        *,
        row_number() over (
            partition by zone_id
            order by
                (case when zone_name is not null then 1 else 0 end)
              + (case when county is not null then 1 else 0 end)
              + (case when dispatch_hub is not null then 1 else 0 end)
              + (case when is_active is not null then 1 else 0 end)
                desc,
                zone_name asc
        ) as row_num
    from cleaned
)

select
    zone_id,
    zone_name,
    county,
    dispatch_hub,
    is_active
from deduped
where row_num = 1