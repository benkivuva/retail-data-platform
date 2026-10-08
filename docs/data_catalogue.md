# Data Catalogue

## Datasets

| Dataset | Purpose | Materialisation |
|---|---|---|
| `raw` | Source CSVs loaded as-is from upstream systems | Tables |
| `staging` | Cleaned and typed source data, one model per source table | Views |
| `intermediate` | Business logic and joins reused by marts | Views |
| `marts` | Final star schema plus metrics table | Tables |

## Key Tables

| Table | Grain | Primary Key | Purpose |
|---|---|---|---|
| `raw.orders` | One row per order | `order_id` | Raw order header from the e-commerce system |
| `staging.stg_orders` | One row per order | `order_id` | Typed and renamed order header |
| `intermediate.int_order_totals` | One row per order | `order_id` | Order header joined to item totals and margin |
| `marts.fct_orders` | One row per order | `order_id` | Business-ready order fact |
| `marts.fct_order_items` | One row per line item | `order_item_id` | Line-level fact |
| `marts.fct_deliveries` | One row per delivery | `delivery_id` | Delivery fact with on-time flag |
| `marts.fct_inventory_snapshots` | One row per product/warehouse/day | composite | Daily inventory position |
| `marts.fct_supplier_orders` | One row per purchase order | `supplier_order_id` | Supplier fulfilment fact |
| `marts.metrics_daily` | One row per calendar day | `metric_date` | Single source of truth for all core metrics |
| `marts.dim_customers` | One row per customer | `customer_id` | Customer dimension |
| `marts.dim_products` | One row per product | `product_id` | Product dimension |
| `marts.dim_suppliers` | One row per supplier | `supplier_id` | Supplier dimension |
| `marts.dim_dates` | One row per calendar day | `date_day` | Date dimension |

## Ownership

| Layer | Owner | Change Process |
|---|---|---|
| Raw ingestion scripts | Analytics Engineering | Pull request |
| Staging models | Analytics Engineering | Pull request + tests |
| Intermediate models | Analytics Engineering | Pull request + tests |
| Marts (facts, dims) | Analytics Engineering + domain owner | Pull request + tests + owner sign-off |
| `metrics_daily` | Analytics Engineering + metric owner | PR + owner sign-off + change note |
| BI dashboards | Domain analysts | PR to dashboard repo |