# Dashboard

**Looker Studio:** <https://datastudio.google.com/reporting/77894e85-444f-4024-a357-0698b6abb93e>

## Data Source

- BigQuery project: `retail-data-platform-511008`
- Dataset: `marts`
- Primary table: `metrics_daily`
- Supporting tables: `fct_orders`, `dim_customers`, `dim_dates`

All charts read from the semantic layer. No metric is recomputed in the dashboard.

## Pages

1. **Operations** — on-time delivery, deliveries, stockouts
2. **Commercial** — GMV, net revenue, AOV, units
3. **Finance** — revenue, discounts, delivery fees, gross margin
4. **Customers** — segments, acquisition channels

## Ownership

Maintained by Analytics Engineering. Metric changes require a pull request to
`metrics_daily.sql` and the metric dictionary.