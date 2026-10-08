# Metric Dictionary

Every metric used in dashboards, reports, or AI assistants must be defined here.
One metric. One definition. One owner.

| Metric | Definition | Formula | Source Model | Owner |
|---|---|---|---|---|
| Total Orders | Count of delivered customer orders | `count(*) where order_status = 'delivered'` | `metrics_daily.total_orders` | Operations |
| GMV | Gross Merchandise Value before discounts | `sum(gross_amount)` | `metrics_daily.gmv` | Commercial |
| Net Revenue | Gross amount minus discounts plus delivery fees | `sum(gross_amount - discount_amount + delivery_fee)` | `metrics_daily.net_revenue` | Finance |
| Total Discount | Sum of all discounts given | `sum(discount_amount)` | `metrics_daily.total_discount` | Commercial |
| Total Delivery Fees | Sum of delivery fees collected | `sum(delivery_fee)` | `metrics_daily.total_delivery_fees` | Finance |
| Total Items | Sum of item counts across orders | `sum(item_count)` | `metrics_daily.total_items` | Operations |
| Total Units | Sum of quantities across order items | `sum(total_quantity)` | `metrics_daily.total_units` | Operations |
| Gross Margin | Items subtotal minus items cost | `sum(items_subtotal - items_cost)` | `metrics_daily.total_gross_margin` | Finance |
| Average Order Value (AOV) | Net revenue per delivered order | `net_revenue / total_orders` | `metrics_daily.average_order_value` | Commercial |
| Deliveries Delivered | Count of completed deliveries (on time or late) | `count(*) where delivery_status in ('delivered', 'delivered_late')` | `metrics_daily.deliveries_delivered` | Operations |
| Deliveries On Time | Count of deliveries where `delivered_at <= promised_at` | `countif(on_time_flag)` | `metrics_daily.deliveries_on_time` | Operations |
| On-Time Delivery Rate | Share of completed deliveries that arrived on time | `deliveries_on_time / deliveries_delivered` | `metrics_daily.on_time_delivery_rate` | Operations |
| Average Delivery Time | Mean minutes from dispatch to delivery | `avg(timestamp_diff(delivered_at, dispatch_at, minute))` | `metrics_daily.avg_delivery_minutes` | Operations |
| Stockout Products | Count of products with `qty_available <= 0` on a day | `countif(stockout_flag)` | `metrics_daily.stockout_products` | Inventory |

## Metric Change Process

Any change to a metric definition requires:

1. A pull request updating the SQL in `models/marts/metrics_daily.sql` and this dictionary.
2. Approval from the metric owner named above.
3. A note in `docs/data_quality_log.md` describing the change, the reason, and the impact.
4. Passing tests including `assert_metrics_daily_within_bounds`.