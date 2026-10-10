# BI Platform

Flask + Plotly Dash application that serves the retail data platform's marts as
interactive dashboards, with authentication, role-based access, and a chat page
backed by the governed Gemini assistant.

This is the code-first serving layer. The pipeline (dbt, Dagster, Soda) produces
the data; this app presents it.

## What it does

- **Four dashboards** — Operations, Commercial, Finance, Customers
- **AI chat** — plain-English questions against `ai/` views via Gemini
- **Auth** — session-based, role-gated (admin / analyst / viewer)
- **CSV-friendly** — every chart is exportable via the Plotly toolbar
- **Read-only** — reads `marts.*` and `ai.*`, never writes, never touches
  `raw`, `staging`, or `intermediate`

## Layout

    platform/
    ├── app/
    │   ├── __init__.py          # create_app() — factory, blueprints, auth gate
    │   ├── config.py            # DevConfig / ProdConfig / BaseConfig
    │   ├── extensions.py        # cache, db, login_manager, csrf
    │   ├── auth/
    │   │   ├── models.py        # User model + role rules (can_view)
    │   │   └── routes.py        # /auth/login, /auth/logout
    │   ├── ai/
    │   │   ├── service.py       # thin wrapper over ai/ask.py
    │   │   └── routes.py        # /ai/chat (page), /ai/ask (JSON)
    │   ├── dashboards/
    │   │   ├── _shared.py       # topbar, KPI cards, chart theming, nav
    │   │   ├── operations.py
    │   │   ├── commercial.py
    │   │   ├── finance.py
    │   │   └── customers.py
    │   ├── queries/
    │   │   └── bigquery.py      # every SQL statement in the app
    │   ├── templates/
    │   │   ├── login.html
    │   │   └── chat.html
    │   └── static/
    │       └── style.css
    ├── tests/
    │   ├── conftest.py
    │   ├── test_auth.py
    │   └── test_ai_allowlist.py
    ├── run.py                   # dev entry point
    └── seed_users.py            # creates demo users

## Configuration

Read from `platform/.env` (loaded by `app/config.py`). Create it with:

    GCP_PROJECT=your-gcp-project-id
    GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
    SECRET_KEY=<random-64-char-string>
    GEMINI_API_KEY=<your-gemini-key>

`SECRET_KEY` signs session cookies. Generate one with:

    python -c "import secrets; print(secrets.token_urlsafe(64))"

## Running locally

Install dependencies (from the repository root):

    uv sync

Seed demo users (only needed once):

    uv run python platform/seed_users.py

Start the dev server:

    uv run python platform/run.py

Open http://127.0.0.1:5000 → redirects to `/auth/login`.

### Demo users

| Email                  | Password     | Role    | Sees |
|------------------------|--------------|---------|------|
| admin@example.com      | admin123     | admin   | Everything |
| analyst@example.com    | analyst123   | analyst | All dashboards |
| viewer@example.com     | viewer123    | viewer  | Operations, Commercial |

Passwords are hashed with werkzeug's `pbkdf2:sha256`. Never use these in
production.

## Running tests

From the repository root:

    uv run pytest platform/tests/ -v

Coverage:

- `test_auth.py` — health is public, protected routes redirect, invalid and
  valid login paths, logout
- `test_ai_allowlist.py` — SELECT on allowed tables passes; DROP, multi-
  statement, and disallowed tables are rejected

Tests use an in-memory SQLite DB and set `REGISTER_DASHBOARDS = False` so no
BigQuery call happens during setup.

## Routes

| Method | Path                        | Purpose |
|--------|-----------------------------|---------|
| GET    | `/`                         | Redirects to `/dashboards/operations/` |
| GET    | `/health`                   | Public JSON health check |
| GET    | `/auth/login`               | Login page |
| POST   | `/auth/login`               | Submit credentials |
| GET    | `/auth/logout`              | Clear session |
| GET    | `/dashboards/operations/`   | Operations dashboard |
| GET    | `/dashboards/commercial/`   | Commercial dashboard |
| GET    | `/dashboards/finance/`      | Finance dashboard |
| GET    | `/dashboards/customers/`    | Customers dashboard |
| GET    | `/ai/chat`                  | AI chat page |
| POST   | `/ai/ask`                   | JSON endpoint — `{ question }` → `{ answer }` |

## Authentication and roles

Session-based. Every request is checked by a `before_request` hook; anything
outside `/auth/*`, `/health`, and `/static/*` requires login.

Roles (see `app/auth/models.py::User::can_view`):

- **admin** — all dashboards
- **analyst** — all dashboards
- **viewer** — Operations and Commercial only

To restrict a dashboard, check `current_user.can_view("<name>")` in the route.

## Session hardening

Configured in `app/config.py`:

- `SESSION_COOKIE_HTTPONLY = True` — JS can't read the session cookie
- `SESSION_COOKIE_SAMESITE = "Lax"` — blocks cross-site POST CSRF
- `SESSION_COOKIE_SECURE` — enabled in `ProdConfig` (HTTPS only)
- `PERMANENT_SESSION_LIFETIME = 8h` — workday session length
- `WTF_CSRF_ENABLED = True` — CSRF token on all forms
- Dash routes are CSRF-exempt (`csrf.exempt("/dashboards/*")`) — they are
  read-only and cannot carry a token
- Login errors are generic ("Invalid email or password") — no user enumeration
- `next=` redirects only accept relative URLs starting with a single `/`

## Data access

All SQL lives in `app/queries/bigquery.py`. Two rules:

1. Dashboards never write SQL — they call a named function.
2. Every query is parameterised and memoised (`@cache.memoize(timeout=300)`).

Functions:

- `get_daily_metrics(days=90)` — feeds Operations, Commercial, Finance
- `get_customer_segments()`, `get_customer_channels()`,
  `get_customer_signups_by_month()` — feed Customers

BigQuery Storage API is disabled (`create_bqstorage_client=False`) so the
service account doesn't need `bigquery.readsessions.create`.

## AI chat

The page at `/ai/chat` posts to `/ai/ask`, which calls
`app/ai/service.py::answer`. That function imports `ask()` from `ai/ask.py` at
the repository root — the same governed assistant used by the CLI. Nothing is
duplicated: same `ai/context.md`, same `is_safe_query()` allowlist, same
allowed views.

If `GEMINI_API_KEY` is missing, `/ai/ask` returns a 500 with a clear message.

## Docker

From WSL (Docker Engine installed inside WSL, no Docker Desktop):

    cd /mnt/c/Users/User/Desktop/RetailDataPlatform
    docker build -t retail-platform .
    docker run --rm -p 8080:8080 \
      -v /mnt/c/keys/retail-data-platform-sa-v2.json:/secrets/sa.json:ro \
      -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json \
      -e GCP_PROJECT=retail-data-platform-511008 \
      -e SECRET_KEY=dev-secret-change-me \
      -e GEMINI_API_KEY=<your-key> \
      -e DATABASE_URL=sqlite:////tmp/platform.db \
      retail-platform

Then open http://localhost:8080/health — should return:

    {"status": "ok", "project": "retail-data-platform-511008"}

Why each flag:

- `-p 8080:8080` — expose container port 8080 to the host
- `-v .../sa.json:/secrets/sa.json:ro` — mount the service account key
  read-only (never bake credentials into the image)
- `-e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json` — where Google libraries
  look for the key inside the container
- `-e DATABASE_URL=sqlite:////tmp/platform.db` — write the SQLite file to
  `/tmp` because `/app` is read-only for the non-root `appuser`

The Dockerfile is a two-stage build: dependencies are installed in a builder
layer, the resulting virtualenv is copied into a slim runtime, and the app runs
as a non-root user under gunicorn.

## Adding a new dashboard

1. Add a query function to `app/queries/bigquery.py` (parameterised, memoised).
2. Create `app/dashboards/<name>.py` following the pattern in
   `operations.py` — define `URL_BASE`, build figures, assemble layout with
   `topbar`, `kpi_card`, `chart_card`, `kpi_row`.
3. Register it in `app/dashboards/_shared.py::NAV_ITEMS` (label + URL).
4. Register it in `app/__init__.py::_register_dashboards`.
5. Update `User::can_view` in `app/auth/models.py` if the role rules change.

## Known limitations

- **Static topbar user label.** The layout is built once at startup, so the
  user label reflects whoever was logged in when the process started, not the
  current request. Logout still works. To make it dynamic per request, add a
  Dash callback that fetches user info from a Flask JSON endpoint.
- **SQLite user store.** Fine for demo; production would use Postgres or an
  identity provider.
- **Single container, no replicas.** Cloud Run / ECS would run multiple
  replicas behind a load balancer; the platform itself is stateless apart from
  the SQLite DB.
- **AI chat is unauthenticated downstream.** The route requires login, but the
  underlying assistant is the same one used by the CLI. Both share the same
  allowlist, so no additional exposure.