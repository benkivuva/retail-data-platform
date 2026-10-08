with date_spine as (
    select date
    from unnest(
        generate_date_array('2025-01-01', '2027-12-31', interval 1 day)
    ) as date
)
select
    date                                    as date_day,
    extract(year from date)                 as year,
    extract(quarter from date)              as quarter,
    extract(month from date)                as month,
    extract(week from date)                 as week,
    extract(day from date)                  as day,
    format_date('%A', date)                 as day_of_week,
    format_date('%B', date)                 as month_name,
    case
        when extract(dayofweek from date) in (1, 7) then true
        else false
    end                                     as is_weekend
from date_spine