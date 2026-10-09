"""Flask application factory."""
from __future__ import annotations

from flask import Flask, redirect, request, url_for
from flask_login import current_user

from .config import DevConfig, ProdConfig
from .extensions import cache, csrf, db, login_manager


def create_app(config_class=DevConfig) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    cache.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    csrf.exempt("/dashboards/*")

    from .auth.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    _register_blueprints(app)
    _register_auth_gate(app)
    _register_dashboards(app)
    _register_core_routes(app)

    with app.app_context():
        db.create_all()

    return app


def _register_blueprints(app: Flask) -> None:
    from .ai.routes import bp as ai_bp
    from .auth.routes import bp as auth_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ai_bp)


def _register_auth_gate(app: Flask) -> None:
    allowed_prefixes = ("/auth/", "/health", "/static/")

    @app.before_request
    def require_login():
        if request.path.startswith(allowed_prefixes):
            return None
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        return None


def _register_dashboards(app: Flask) -> None:
    from .dashboards.commercial import init_commercial_dashboard
    from .dashboards.customers import init_customers_dashboard
    from .dashboards.finance import init_finance_dashboard
    from .dashboards.operations import init_operations_dashboard

    init_operations_dashboard(app)
    init_commercial_dashboard(app)
    init_finance_dashboard(app)
    init_customers_dashboard(app)


def _register_core_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return redirect("/dashboards/operations/")

    @app.route("/health")
    def health():
        return {"status": "ok", "project": app.config["GCP_PROJECT"]}