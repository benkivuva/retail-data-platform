with orders as (
    select
        order_date,
        order_status,
        channel,
        gross_amount,
        discount_amount,
        delivery_fee,
        net_revenue,
        item_count,
        total_quantity,
        gross_margin
    from {{ ref('fct_orders') }}
    where order_status = 'delivered'
),

deliveries as (
    -- A delivery is "completed" if it arrived, whether on time or late.
    -- 'failed' deliveries are excluded because the customer never received goods.
    select
        date(delivered_at)         as delivery_date,
        on_time_flag,
        delivery_minutes
    from {{ ref('fct_deliveries') }}
    where delivery_status in ('delivered', 'delivered_late')
),

inventory as (
    select
        snapshot_date,
        countif(stockout_flag)     as stockout_products
    from {{ ref('fct_inventory_snapshots') }}
    group by snapshot_date
),

orders_by_day as (
    select
        order_date                                           as metric_date,
        count(*)                                             as total_orders,
        sum(gross_amount)                                    as gmv,
        sum(net_revenue)                                     as net_revenue,
        sum(discount_amount)                                 as total_discount,
        sum(delivery_fee)                                    as total_delivery_fees,
        sum(item_count)                                      as total_items,
        sum(total_quantity)                                  as total_units,
        sum(gross_margin)                                    as total_gross_margin,
        safe_divide(sum(net_revenue), count(*))              as average_order_value
    from orders
    group by order_date
),

deliveries_by_day as (
    select
        delivery_date                                        as metric_date,
        count(*)                                             as deliveries_delivered,
        countif(on_time_flag)                                as deliveries_on_time,
        safe_divide(countif(on_time_flag), count(*))         as on_time_delivery_rate,
        avg(delivery_minutes)                                as avg_delivery_minutes
    from deliveries
    group by delivery_date
),

inventory_by_day as (
    select
        snapshot_date                                        as metric_date,
        stockout_products
    from inventory
)

select
    coalesce(o.metric_date, d.metric_date, i.metric_date)   as metric_date,
    coalesce(o.total_orders, 0)                              as total_orders,
    coalesce(o.gmv, 0)                                       as gmv,
    coalesce(o.net_revenue, 0)                               as net_revenue,
    coalesce(o.total_discount, 0)                            as total_discount,
    coalesce(o.total_delivery_fees, 0)                       as total_delivery_fees,
    coalesce(o.total_items, 0)                               as total_items,
    coalesce(o.total_units, 0)                               as total_units,
    coalesce(o.total_gross_margin, 0)                        as total_gross_margin,
    o.average_order_value,
    coalesce(d.deliveries_delivered, 0)                      as deliveries_delivered,
    coalesce(d.deliveries_on_time, 0)                        as deliveries_on_time,
    d.on_time_delivery_rate,
    d.avg_delivery_minutes,
    coalesce(i.stockout_products, 0)                         as stockout_products
from orders_by_day o
full outer join deliveries_by_day d using (metric_date)
full outer join inventory_by_day i using (metric_date)