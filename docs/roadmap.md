# Roadmap

What is not built yet, and why. This is what I would work on next if the
platform moved from portfolio to production.

## Near term (next 1–2 weeks)

### Alerting on test failures
CI blocks bad merges, but there is no runtime alerting. Add a scheduled job
that runs `dbt build` nightly and posts failures to a Slack channel. That is
the difference between "tests exist" and "issues are caught before the business
sees them."

### Freshness SLAs per source
Track when each raw table was last loaded. Fail if `orders` is older than
24 hours, `inventory_snapshots` older than 6 hours. Use dbt `source freshness`.

### Cost guardrails
Add `maximum_bytes_billed` to the dbt profile so runaway queries are capped
rather than billed. Add the monitoring query from `cost_report.md` to a weekly
review.

### Partitioning and clustering
Partition `fct_orders`, `fct_deliveries`, and `fct_order_items` by date.
Cluster by `product_id` and `customer_id`. This alone typically cuts scanned
bytes by 60–80% on date-filtered queries.

## Medium term (next 1–2 months)

### Orchestration
Right now the pipeline runs when someone types `dbt build`. In production it
should run on a schedule. Options:

- dbt Cloud jobs (lowest effort)
- Cloud Composer / Airflow (more control)
- Cloud Run + Cloud Scheduler (cheapest)

### Auto-generated AI context
`ai/context.md` is written by hand. dbt already produces a manifest with every
model description, column description, and metric. Generate the AI context
from the manifest so definitions never drift.

### Model-agnostic AI layer
The current assistant uses Gemini. The `run_sql` tool, allowlist, and context
document are model-agnostic. Adding Claude or GPT is a small adapter, not a
rewrite. The bigger win is exposing the same tool via MCP so Claude Desktop
and other clients can connect without code changes.

### Data catalogue integration
The catalogue is a markdown file. In production this belongs in a real
catalogue (DataHub, OpenMetadata, or dbt Cloud's built-in catalogue) with
search, ownership tags, and automatic lineage from the dbt manifest.

## Long term (next 3–6 months)

### Streaming / near-real-time
Current pipeline is batch. If operations need sub-15-minute visibility on
delivery status, add a streaming path for `deliveries` via Pub/Sub and
BigQuery streaming inserts, keeping the batch path for historical recompute.

### Cost attribution per team
Tag queries by team so dashboard cost can be attributed. Enables conversations
like "this Finance dashboard scans 4 TB per day; here is a cheaper version."

### Data contracts for source systems
The JD mentions raising issues with Tech when source systems change. Formalize
this with data contracts: schema version, required columns, freshness SLA,
and a test that fails when the contract is broken upstream.

### Access controls via IAM, not just views
The `ai` dataset is PII-free, which is safe but blunt. Add column-level
security tags so a broader audience can access `marts` safely with automatic
masking of email, phone, and address.

## What is explicitly not planned

- A custom BI tool. Looker Studio and Power BI already work.
- A custom query engine. BigQuery is the warehouse.
- An LLM. Use the providers; build the governance layer around them.

## Ownership

Analytics Engineering owns this roadmap. Priorities are reviewed monthly with
the business leads who consume the data.