# Retail Data Platform

An end-to-end analytics engineering platform for an online supermarket. Ingests
raw operational data, models it into a trusted star schema in BigQuery, defines
core metrics once, and serves them through a Flask + Plotly Dash BI platform,
Looker Studio, and a governed AI assistant.

The project includes a real data-quality incident (on-time delivery rate
silently reporting 100%), diagnosed, fixed, and covered by a regression test.
See [docs/data_quality_log.md](docs/data_quality_log.md).

## Architecture

    raw (CSV) -> staging -> intermediate -> marts
                                             |-- dimensions
                                             |-- facts
                                             |-- metrics_daily
                                             |-- mon_pipeline_health
                                             |
                                             +-> ai (PII-free views)

Serving layers (all read from `marts` or `ai`):

    marts / ai  ->  Flask + Plotly Dash   (4 dashboards + AI chat)
                ->  Looker Studio         (5-page business dashboard)
                ->  Gemini assistant      (governed SQL, allowlist-protected)

Lineage:

![lineage](docs/lineage.png)

## Stack

- **Warehouse:** Google BigQuery
- **Transformation:** dbt Core with `dbt-bigquery`
- **Orchestration:** Dagster (daily schedule, asset-level observability)
- **Data Quality:** dbt tests (in-warehouse) + Soda Core (anomaly detection)
- **Language:** SQL, Python
- **Environment:** `uv` for Python and dependency management
- **BI (hosted):** Looker Studio
- **BI (application):** Flask 3 + Plotly Dash 4, served by gunicorn
- **Auth:** Flask-Login with role-based access (admin / analyst / viewer)
- **AI:** Google Gemini with a governed SQL tool
- **Containerisation:** Docker (multi-stage, non-root user)
- **CI/CD:** GitHub Actions (two workflows: pipeline + platform)
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

Two complementary layers:

**dbt tests (in-warehouse)** — 111 automated tests covering:

- Primary and foreign key checks
- Custom business rules (order reconciliation, delivery timing, inventory
  bounds, payment limits)
- Metric bounds on `metrics_daily`

**Soda Core (raw-layer anomaly detection)** — 10 checks on the raw dataset:

- Row count is never zero
- Duplicate and missing IDs on primary keys
- Negative financial values (revenue, discount, quantity)
- Row-count thresholds for anomaly detection

The Soda scan runs as a downstream Dagster asset; a failed scan fails the
pipeline. See `soda/checks.yml`.

## Monitoring

Three layers cover pipeline health:

- **Dagster UI** — per-asset run status, timing, and error logs for every dbt
  build and Soda scan
- **Soda Core** — anomaly detection on the raw layer
- **Looker Studio (Pipeline Health page)** — freshness lag, row counts, and
  latest metric date, read from `marts.mon_pipeline_health`

## Looker Studio Dashboard

A five-page Looker Studio dashboard reads directly from `marts`:

- **Operations** — orders, deliveries, on-time rate, stockouts
- **Commercial** — GMV, net revenue, AOV, units
- **Finance** — revenue, discounts, delivery fees, gross margin
- **Customers** — segments, acquisition channels
- **Pipeline Health** — freshness lag, row counts, latest metric date

Link: [dashboards/dashboard_link.md](dashboards/dashboard_link.md)

## BI Platform

A Flask + Plotly Dash application in `platform/` provides a code-first BI
surface on top of the same metrics:

- **Four dashboards** — Operations, Commercial, Finance, Customers
- **AI chat** at `/ai/chat` — plain-English queries against the governed
  assistant in `ai/`
- **Authentication** — session-based via Flask-Login; role-based access
  (admin, analyst, viewer)
- **Session hardening** — CSRF protection, HTTPOnly + SameSite cookies,
  8-hour session lifetime, open-redirect protection on `next=`
- **Caching** — 5-minute TTL on BigQuery queries to keep the UI responsive
- **Containerised** — multi-stage Dockerfile, non-root user, gunicorn
- **Tested** — pytest suite covering the auth flow and the AI SQL allowlist

Data access is centralised in `platform/app/queries/bigquery.py`. The platform
reads `marts.*` and `ai.*` only — never `raw`, `staging`, or `intermediate`,
and never writes.

Run locally:

    uv run python platform/run.py

Seed demo users (admin@example.com / admin123, analyst@..., viewer@...):

    uv run python platform/seed_users.py

Run in Docker (build from WSL; mount service account, pass secrets via env):

    docker build -t retail-platform .
    docker run --rm -p 8080:8080 \
      -v /path/to/sa.json:/secrets/sa.json:ro \
      -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json \
      -e GCP_PROJECT=<your-project> \
      -e SECRET_KEY=<random-string> \
      -e GEMINI_API_KEY=<your-key> \
      -e DATABASE_URL=sqlite:////tmp/platform.db \
      retail-platform

## Orchestration

Dagster orchestrates the full pipeline as an asset graph: one Dagster asset per
dbt model plus a downstream Soda scan. A daily 6 AM schedule triggers the run.
dbt tests halt downstream models on failure, and a failed Soda scan fails the
run. Every execution is tracked in the Dagster UI with per-asset status, timing,
and error logs.

![Dagster DAG](docs/dagster_lineage.png)

Successful materialization of all assets:

![Dagster run](docs/dagster_run.png)

Run locally:

    uv run dagster dev -f orchestration/definitions.py

In production this would deploy to Dagster+ or a scheduled VM; here it runs in
dev mode for demonstration.

## AI Assistant

A governed AI assistant lets users ask business questions in plain English.
The model (`gemini-3.8-flash`) reads `ai/context.md` as system instructions,
generates a BigQuery SQL query, and calls a `run_sql` tool. Every query passes
an allowlist that:

- Permits only SELECT statements
- Blocks multiple statements
- Restricts access to three PII-free views: `ai_daily_metrics`,
  `ai_customers_summary`, `ai_products_summary`

The assistant is available two ways: as a CLI (`ai/ask.py`) and as a web page
inside the BI platform (`/ai/chat`). The allowlist is covered by unit tests in
`platform/tests/test_ai_allowlist.py`, run on every push. The assistant itself
is not exercised in CI because it requires an API key and live network access.

See [ai/context.md](ai/context.md) and [ai/ask.py](ai/ask.py).

## CI/CD

Two GitHub Actions workflows run on every push to `main` and every pull request:

- **`dbt_ci.yml`** — writes BigQuery credentials from GitHub Secrets, runs
  `dbt debug`, `dbt build`, and the pipeline unit tests.
- **`platform_ci.yml`** — installs dependencies, runs the platform pytest
  suite (auth flow, AI SQL allowlist), and builds the Docker image.

Failed tests or a failed image build block the merge.

## Getting Started

1. Install `uv`, `gcloud`, and Python 3.12.
2. Set up a GCP project with datasets `raw`, `staging`, `intermediate`, `marts`, `ai`.
   The `ai` dataset is created automatically by dbt on first build, or manually
   with `bq mk --location=US ai`.
3. Create a service account with BigQuery Data Editor and Job User roles.
4. Configure `~/.dbt/profiles.yml` with the service account key.
5. Generate synthetic data and load it from the repository root:

       uv run python data/scripts/generate_raw_data.py
       uv run python data/scripts/load_raw_to_bigquery.py

6. Build the whole warehouse:

       cd dbt
       uv run dbt build --full-refresh

7. Generate and view dbt docs:

       uv run dbt docs generate
       uv run dbt docs serve

8. Optional — run the pipeline under Dagster:

       uv run dagster dev -f orchestration/definitions.py

9. Optional — run Soda checks standalone:

       uv run soda scan -d retail_bigquery -c soda/configuration.yml soda/checks.yml

10. Optional — run the BI platform locally (requires `platform/.env`):

        uv run python platform/run.py
        uv run python platform/seed_users.py

11. Optional — run the CLI AI assistant:

        $env:GEMINI_API_KEY = "your-key"
        uv run python ai/ask.py

## Documentation

- [Architecture](docs/architecture.md)
- [Metric Dictionary](docs/metric_dictionary.md)
- [Data Catalogue](docs/data_catalogue.md)
- [Runbook](docs/runbook.md)
- [Data Quality Log](docs/data_quality_log.md)
- [Cost Report](docs/cost_report.md)
- [Roadmap](docs/roadmap.md)
- [Dashboard](dashboards/dashboard_link.md)
- [AI Context](ai/context.md)

## Repository Layout

    RetailDataPlatform/
    ├── .github/
    │   └── workflows/
    │       ├── dbt_ci.yml           # Pipeline: dbt build + tests
    │       └── platform_ci.yml      # Platform: pytest + Docker build
    ├── ai/
    │   ├── ask.py                   # Gemini assistant with SQL allowlist
    │   └── context.md               # definitions and query rules for the AI
    ├── dashboards/
    │   └── dashboard_link.md        # Looker Studio dashboard
    ├── data/
    │   ├── raw/                     # CSVs (gitignored)
    │   └── scripts/                 # generators and loaders
    ├── dbt/
    │   ├── macros/                  # generate_schema_name
    │   ├── models/
    │   │   ├── staging/
    │   │   ├── intermediate/
    │   │   ├── marts/               # dims, facts, metrics_daily, mon_pipeline_health
    │   │   └── ai/
    │   └── tests/                   # custom singular tests
    ├── docs/
    ├── orchestration/
    │   └── definitions.py           # Dagster assets + daily schedule + Soda scan
    ├── platform/
    │   ├── app/
    │   │   ├── auth/                # login, role model, session hardening
    │   │   ├── ai/                  # chat page wired to governed assistant
    │   │   ├── dashboards/          # Operations, Commercial, Finance, Customers
    │   │   ├── queries/             # BigQuery access layer
    │   │   └── templates/           # login + chat pages
    │   ├── tests/                   # pytest for auth + AI allowlist
    │   ├── run.py                   # dev entry point
    │   └── seed_users.py            # creates demo users
    ├── soda/
    │   ├── configuration.yml        # Soda BigQuery connection
    │   └── checks.yml               # 10 anomaly + validation checks
    ├── Dockerfile                   # multi-stage, non-root, gunicorn
    ├── wsgi.py                      # production entry point
    └── pyproject.toml