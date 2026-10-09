"""Flask application factory."""
from __future__ import annotations

from flask import Flask, redirect

from .config import DevConfig, ProdConfig
from .extensions import cache


def create_app(config_class=DevConfig) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    cache.init_app(app)

    _register_dashboards(app)
    _register_core_routes(app)

    return app


def _register_dashboards(app: Flask) -> None:
    """Mount each Dash dashboard on the Flask server."""
    from .dashboards.operations import init_operations_dashboard

    init_operations_dashboard(app)


def _register_core_routes(app: Flask) -> None:
    """App-level routes: root redirect and health check."""

    @app.route("/")
    def index():
        return redirect("/dashboards/operations/")

    @app.route("/health")
    def health():
        return {"status": "ok", "project": app.config["GCP_PROJECT"]}