select
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    signup_date,
    acquisition_channel,
    segment
from {{ ref('stg_customers') }}