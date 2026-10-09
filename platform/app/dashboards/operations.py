"""Operations dashboard — orders, deliveries, stockouts."""
from __future__ import annotations

import plotly.express as px
from dash import Dash, html
from flask import Flask

from ..queries.bigquery import get_daily_metrics
from ._shared import (
    ACCENT,
    PAGE_STYLE,
    PRIMARY,
    PURPLE,
    WARN,
    chart_card,
    kpi_card,
    kpi_row,
    style_figure,
    topbar,
)

URL_BASE = "/dashboards/operations/"


def init_operations_dashboard(server: Flask) -> Dash:
    """Mount the operations dashboard on the given Flask app."""
    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname=URL_BASE,
        title="Operations | Retail Data Platform",
    )

    with server.app_context():
        df = get_daily_metrics(days=90)

    total_orders = int(df["total_orders"].sum())
    avg_on_time = float(df["on_time_delivery_rate"].mean())
    avg_delivery = float(df["avg_delivery_minutes"].mean())
    avg_stockouts = float(df["stockout_products"].mean())

    orders_fig = style_figure(
        px.line(df, x="metric_date", y="total_orders",
                color_discrete_sequence=[PRIMARY])
    )
    orders_fig.update_traces(line=dict(width=2))

    on_time_fig = style_figure(
        px.line(df, x="metric_date", y="on_time_delivery_rate",
                color_discrete_sequence=[ACCENT])
    )
    on_time_fig.update_traces(line=dict(width=2))
    on_time_fig.update_yaxes(tickformat=".0%", range=[0, 1])

    stockout_fig = style_figure(
        px.bar(df, x="metric_date", y="stockout_products",
               color_discrete_sequence=[WARN])
    )

    dash_app.layout = html.Div(
        [
            topbar(current_path=URL_BASE),
            html.Div(
                [
                    html.H1("Operations Dashboard",
                            style={"fontSize": "24px", "fontWeight": "700",
                                   "margin": "0 0 4px 0"}),
                    html.P("Last 90 days · sourced from marts.metrics_daily",
                           style={"color": "#64748b", "fontSize": "14px",
                                  "margin": "0 0 24px 0"}),
                    kpi_row([
                        kpi_card("Total Orders", f"{total_orders:,}",
                                 "delivered orders", PRIMARY),
                        kpi_card("On-Time Rate", f"{avg_on_time:.1%}",
                                 "90-day average", ACCENT),
                        kpi_card("Avg Delivery", f"{avg_delivery:.0f} min",
                                 "dispatch to delivered", PURPLE),
                        kpi_card("Stockouts / Day", f"{avg_stockouts:.1f}",
                                 "products unavailable", WARN),
                    ]),
                    chart_card("Orders per day",
                               "Volume trend across the period", orders_fig),
                    chart_card("On-time delivery rate",
                               "Share of deliveries arriving by promise time",
                               on_time_fig),
                    chart_card("Products out of stock",
                               "Daily count of SKUs with zero availability",
                               stockout_fig),
                ],
                style={"padding": "24px", "maxWidth": "1400px",
                       "margin": "0 auto"},
            ),
        ],
        style=PAGE_STYLE,
    )

    return dash_app