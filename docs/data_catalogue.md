# Data Catalogue

## Datasets

| Dataset | Purpose | Materialisation |
|---|---|---|
| `raw` | Source CSVs and ops Google Sheets loaded as-is | Tables |
| `staging` | Cleaned and typed source data, one model per source table | Views |
| `intermediate` | Business logic and joins reused by marts | Views |
| `marts` | Final star schema plus metrics and monitoring tables | Tables |
| `ai` | PII-free, read-only views for AI assistants | Views |

## Key Tables

### Raw (`raw`)

| Table | Grain | Primary Key | Source |
|---|---|---|---|
| `raw.orders` | One row per order | `order_id` | CSV generator |
| `raw.order_items` | One row per line item | `order_item_id` | CSV generator |
| `raw.payments` | One row per payment | `payment_id` | CSV generator |
| `raw.deliveries` | One row per delivery | `delivery_id` | CSV generator |
| `raw.inventory_snapshots` | One row per product/warehouse/day | composite | CSV generator |
| `raw.products` | One row per product | `product_id` | CSV generator |
| `raw.customers` | One row per customer | `customer_id` | CSV generator |
| `raw.suppliers` | One row per supplier | `supplier_id` | CSV generator |
| `raw.supplier_orders` | One row per purchase order | `supplier_order_id` | CSV generator |
| `raw.ops_zone_master` | One row per delivery zone | `zone_id` | Ops Google Sheet (dirty) |
| `raw.ops_driver_roster` | One row per driver-day assignment | composite | Ops Google Sheet (dirty) |
| `raw.ops_vehicle_log` | One row per service event | composite | Ops Google Sheet (dirty) |

### Staging (`staging`)

| Table | Grain | Primary Key | Notes |
|---|---|---|---|
| `staging.stg_orders` | One row per order | `order_id` | Types cast, columns renamed |
| `staging.stg_order_items` | One row per line item | `order_item_id` | |
| `staging.stg_payments` | One row per payment | `payment_id` | |
| `staging.stg_deliveries` | One row per delivery | `delivery_id` | `ZN001` → `Z001` zone reconciliation applied |
| `staging.stg_inventory_snapshots` | One row per product/warehouse/day | composite | |
| `staging.stg_products` | One row per product | `product_id` | |
| `staging.stg_customers` | One row per customer | `customer_id` | Contains PII — restricted access |
| `staging.stg_suppliers` | One row per supplier | `supplier_id` | |
| `staging.stg_supplier_orders` | One row per purchase order | `supplier_order_id` | |
| `staging.stg_ops_zone_master` | One row per zone | `zone_id` | Counties standardised, `Active?` cast to boolean, duplicates deduped |
| `staging.stg_ops_driver_roster` | One row per driver-day | composite | Dates parsed, phones normalised to E.164, unknown zones flagged |
| `staging.stg_ops_vehicle_log` | One row per service event | composite | Registrations normalised, descriptions classified, cost parsed to NUMERIC |

### Intermediate (`intermediate`)

| Table | Grain | Primary Key | Purpose |
|---|---|---|---|
| `intermediate.int_order_totals` | One row per order | `order_id` | Order header joined to item totals and margin |
| `intermediate.int_delivery_times` | One row per delivery | `delivery_id` | Dispatch and delivery timing, on-time flag |
| `intermediate.int_inventory_movements` | One row per product/warehouse/day | composite | Day-over-day change, stockout flag |
| `intermediate.int_supplier_lead_times` | One row per purchase order | `supplier_order_id` | Actual lead days and fill rate |

### Marts — Facts (`marts.fct_*`)

| Table | Grain | Primary Key | Purpose |
|---|---|---|---|
| `marts.fct_orders` | One row per order | `order_id` | Business-ready order fact with financials |
| `marts.fct_order_items` | One row per line item | `order_item_id` | Line-level fact |
| `marts.fct_deliveries` | One row per delivery | `delivery_id` | Delivery fact with on-time flag |
| `marts.fct_inventory_snapshots` | One row per product/warehouse/day | composite | Daily inventory position |
| `marts.fct_supplier_orders` | One row per purchase order | `supplier_order_id` | Supplier fulfilment fact |

### Marts — Dimensions (`marts.dim_*`)

| Table | Grain | Primary Key | Source |
|---|---|---|---|
| `marts.dim_customers` | One row per customer | `customer_id` | `stg_customers` |
| `marts.dim_products` | One row per product | `product_id` | `stg_products` + supplier name |
| `marts.dim_suppliers` | One row per supplier | `supplier_id` | `stg_suppliers` |
| `marts.dim_delivery_zones` | One row per zone | `zone_id` | `stg_ops_zone_master` — includes county and dispatch hub |
| `marts.dim_drivers` | One row per driver | `driver_id` (md5 hash) | `stg_ops_driver_roster` — most recent phone, assignment counts |
| `marts.dim_vehicles` | One row per vehicle | `vehicle_reg` | `stg_ops_vehicle_log` — service history, total maintenance cost |
| `marts.dim_warehouses` | One row per warehouse | `warehouse_id` | `stg_orders` |
| `marts.dim_dates` | One row per calendar day | `date_day` | Date spine 2025-01-01 to 2027-12-31 |

### Marts — Semantic and Monitoring

| Table | Grain | Primary Key | Purpose |
|---|---|---|---|
| `marts.metrics_daily` | One row per calendar day | `metric_date` | Single source of truth for all core metrics |
| `marts.mon_pipeline_health` | One row per run | `checked_at` | Freshness lag, row counts, latest metric date |

### AI (`ai`)

| Table | Grain | Primary Key | Purpose |
|---|---|---|---|
| `ai.ai_daily_metrics` | One row per calendar day | `metric_date` | PII-free daily metrics for the AI assistant |
| `ai.ai_customers_summary` | One row per segment × channel | composite | Aggregated customer counts, no PII |
| `ai.ai_products_summary` | One row per category | `category` | Aggregated product counts and prices, no PII |

## PII map

Personal data exists only in `staging.stg_customers` and `marts.dim_customers`:

| Column | Stored in | Handling |
|---|---|---|
| `first_name`, `last_name` | `stg_customers`, `dim_customers` | Never selected by any fact, AI view, or dashboard query |
| `email` | `stg_customers`, `dim_customers` | Same |
| `phone` | `stg_customers`, `dim_customers` | Same |
| `city` | `stg_customers`, `dim_customers` | Available for aggregation only |

Ops sheet driver names and phone numbers live in `raw.ops_driver_roster`,
`staging.stg_ops_driver_roster`, and `marts.dim_drivers`. These are internal
operational data (staff assignments), not customer PII, and are not exposed
to the `ai` dataset or the AI assistant.

## Ownership

| Layer | Owner | Change Process |
|---|---|---|
| Raw ingestion scripts | Analytics Engineering | Pull request |
| Ops Google Sheet (source) | Operations | Edit in place; changes flow through next pipeline run |
| Staging models | Analytics Engineering | Pull request + tests |
| Intermediate models | Analytics Engineering | Pull request + tests |
| Marts (facts, dims) | Analytics Engineering + domain owner | Pull request + tests + owner sign-off |
| `metrics_daily` | Analytics Engineering + metric owner | PR + owner sign-off + change note |
| `mon_pipeline_health` | Analytics Engineering | Pull request + tests |
| AI views and assistant | Analytics Engineering | PR + unit tests |
| Flask + Dash platform | Analytics Engineering | PR + pytest + Docker build |
| Looker Studio dashboards | Domain analysts | PR to dashboard repo |

## Access tiers

| Tier | Dataset | Who |
|---|---|---|
| Source | `raw` | Analytics Engineering only |
| Cleaned | `staging` | Analytics Engineering |
| Modelled | `intermediate` | Analytics Engineering |
| Served | `marts` | Analytics Engineering (write), BI team (read) |
| Self-serve | `marts.metrics_daily`, `marts.dim_dates` | Business analysts, external reporting |
| AI / PII-free | `ai` | AI assistant, partner organizations, any authenticated user |

Full policy in [access_control.md](access_control.md).