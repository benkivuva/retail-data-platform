"""Operations dashboard — orders, deliveries, stockouts."""
from __future__ import annotations

import plotly.express as px
from dash import Dash, dcc, html
from flask import Flask

from ..queries.bigquery import get_daily_metrics

_PAGE_STYLE = {"padding": "24px", "fontFamily": "system-ui, sans-serif"}
_CHART_STYLE = {"marginBottom": "24px"}


def init_operations_dashboard(server: Flask) -> Dash:
    """Mount the operations dashboard on the given Flask app."""
    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname="/dashboards/operations/",
        title="Operations | Retail Data Platform",
    )

    with server.app_context():
        df = get_daily_metrics(days=90)

    dash_app.layout = html.Div(
        [
            html.H1("Operations"),
            html.P("Last 90 days, sourced from marts.metrics_daily."),
            dcc.Graph(
                figure=px.line(df, x="metric_date", y="total_orders",
                               title="Orders per day"),
                style=_CHART_STYLE,
            ),
            dcc.Graph(
                figure=px.line(df, x="metric_date", y="on_time_delivery_rate",
                               title="On-time delivery rate"),
                style=_CHART_STYLE,
            ),
            dcc.Graph(
                figure=px.bar(df, x="metric_date", y="stockout_products",
                              title="Products out of stock"),
                style=_CHART_STYLE,
            ),
        ],
        style=_PAGE_STYLE,
    )

    return dash_app