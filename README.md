# Retail Data Platform

An end-to-end analytics engineering platform for an online supermarket. Ingests
raw operational data, models it into a trusted star schema in BigQuery, defines
core metrics once, and serves them to BI tools and AI assistants.

## Architecture

    raw (CSV) -> staging (views) -> intermediate (views) -> marts (tables)
                                                              |-- dimensions
                                                              |-- facts
                                                              |-- metrics_daily
                                                              |-- ai views (PII-free)

Lineage:

![lineage](docs/lineage.png)

## Stack

- **Warehouse:** Google BigQuery
- **Transformation:** dbt Core with `dbt-bigquery`
- **Language:** SQL, Python
- **Environment:** `uv` for Python and dependency management
- **BI:** Looker Studio
- **AI:** Google Gemini with governed SQL tool
- **CI/CD:** GitHub Actions
- **Version control:** Git, feature-branch workflow

## Datasets

| Dataset | Purpose |
|---|---|
| `raw` | Source CSVs loaded as-is |
| `staging` | Cleaned and typed source data |
| `intermediate` | Business logic reused by marts |
| `marts` | Star schema and metrics |
| `ai` | PII-free, read-only views for AI assistants |

## Core Metrics

All metrics are defined once in `marts.metrics_daily`. See
[docs/metric_dictionary.md](docs/metric_dictionary.md) for definitions,
formulas, owners, and the change process.

## Data Quality

111 automated tests including:

- Primary and foreign key checks
- Custom business rules (order reconciliation, delivery timing, inventory bounds, payment limits)
- Metric bounds on `metrics_daily`

See [docs/data_quality_log.md](docs/data_quality_log.md) for a real incident
that was diagnosed, fixed, and covered by a regression test.

## Dashboard

A four-page Looker Studio dashboard reads directly from `marts.metrics_daily`:

- **Operations** — orders, deliveries, on-time rate, stockouts
- **Commercial** — GMV, net revenue, AOV, units
- **Finance** — revenue, discounts, delivery fees, gross margin
- **Customers** — segments, acquisition channels

Link: [dashboards/dashboard_link.md](dashboards/dashboard_link.md)

## AI Assistant

A governed AI assistant lets users ask business questions in plain English.
The model (`gemini-3.8-flash`) reads `ai/context.md` as system instructions,
generates a BigQuery SQL query, and calls a `run_sql` tool. Every query passes
an allowlist that:

- Permits only SELECT statements
- Blocks multiple statements
- Restricts access to three PII-free views: `ai_daily_metrics`,
  `ai_customers_summary`, `ai_products_summary`

See [ai/context.md](ai/context.md) for definitions and query rules, and
[ai/ask.py](ai/ask.py) for the implementation.

## CI/CD

Every push to `main` and every pull request runs `dbt build` in GitHub Actions.
The workflow installs dependencies, writes BigQuery credentials from GitHub
secrets, runs `dbt debug`, and executes the full test suite. Failed tests block
the merge.

See [.github/workflows/dbt_ci.yml](.github/workflows/dbt_ci.yml).

## Getting Started

1. Install `uv`, `gcloud`, and Python 3.12.
2. Set up a GCP project with datasets `raw`, `staging`, `intermediate`, `marts`.
3. Create a service account with BigQuery Data Editor and Job User roles.
4. Configure `~/.dbt/profiles.yml` with the service account key.
5. Generate synthetic data and load it from the repository root:

       uv run python data/scripts/generate_raw_data.py
       uv run python data/scripts/load_raw_to_bigquery.py

6. Build the whole warehouse:

       cd dbt
       uv run dbt build --full-refresh

7. Generate and view docs:

       uv run dbt docs generate
       uv run dbt docs serve

8. Optional — run the AI assistant:

       $env:GEMINI_API_KEY = "your-key"
       uv run python ai/ask.py

## Documentation

- [Metric Dictionary](docs/metric_dictionary.md)
- [Data Catalogue](docs/data_catalogue.md)
- [Runbook](docs/runbook.md)
- [Data Quality Log](docs/data_quality_log.md)
- [Dashboard](dashboards/dashboard_link.md)
- [AI Context](ai/context.md)

## Repository Layout

    RetailDataPlatform/
    ├── .github/
    │   └── workflows/
    │       └── dbt_ci.yml       # GitHub Actions CI
    ├── ai/
    │   ├── ask.py               # Gemini assistant with SQL allowlist
    │   └── context.md           # definitions and query rules for the AI
    ├── dashboards/
    │   └── dashboard_link.md    # Looker Studio dashboard
    ├── data/
    │   ├── raw/                 # CSVs (gitignored)
    │   └── scripts/             # generators and loaders
    ├── dbt/
    │   ├── macros/              # generate_schema_name
    │   ├── models/
    │   │   ├── staging/
    │   │   ├── intermediate/
    │   │   ├── marts/
    │   │   └── ai/
    │   └── tests/               # custom singular tests
    ├── docs/
    └── pyproject.toml