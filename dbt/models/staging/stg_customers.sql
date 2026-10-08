select
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    cast(signup_date as date)   as signup_date,
    acquisition_channel,
    segment
from {{ source('raw', 'customers') }}
