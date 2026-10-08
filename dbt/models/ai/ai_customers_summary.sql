{{ config(materialized='view', schema='ai') }}

select
    segment,
    acquisition_channel,
    count(*) as customer_count
from {{ ref('dim_customers') }}
group by segment, acquisition_channel