# ---------- build stage ----------
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv
# --no-install-project: skip installing this repo as a package (it isn't one)
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv sync --frozen --no-dev --no-install-project

# ---------- runtime stage ----------
FROM python:3.12-slim

# Non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy the built virtualenv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY platform/ ./platform/
COPY ai/ ./ai/
COPY wsgi.py ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "wsgi:app"]