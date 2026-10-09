"""Commercial dashboard — GMV, net revenue, AOV, units."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
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

URL_BASE = "/dashboards/commercial/"


def init_commercial_dashboard(server: Flask) -> Dash:
    """Mount the commercial dashboard on the given Flask app."""
    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname=URL_BASE,
        title="Commercial | Retail Data Platform",
    )

    with server.app_context():
        df = get_daily_metrics(days=90)

    total_gmv = float(df["gmv"].sum())
    total_net = float(df["net_revenue"].sum())
    avg_aov = float(df["average_order_value"].mean())
    total_units = int(df["total_units"].sum())

    # Revenue trend: GMV and Net on the same axes for comparison.
    revenue_fig = go.Figure()
    revenue_fig.add_trace(go.Scatter(
        x=df["metric_date"], y=df["gmv"], name="GMV",
        mode="lines", line=dict(color=PRIMARY, width=2),
    ))
    revenue_fig.add_trace(go.Scatter(
        x=df["metric_date"], y=df["net_revenue"], name="Net Revenue",
        mode="lines", line=dict(color=ACCENT, width=2),
    ))
    style_figure(revenue_fig)
    revenue_fig.update_layout(legend=dict(orientation="h", y=1.1, x=0))

    aov_fig = style_figure(
        px.line(df, x="metric_date", y="average_order_value",
                color_discrete_sequence=[PURPLE])
    )
    aov_fig.update_traces(line=dict(width=2))

    units_fig = style_figure(
        px.bar(df, x="metric_date", y="total_units",
               color_discrete_sequence=[WARN])
    )

    dash_app.layout = html.Div(
        [
            topbar(current_path=URL_BASE),
            html.Div(
                [
                    html.H1("Commercial Dashboard",
                            style={"fontSize": "24px", "fontWeight": "700",
                                   "margin": "0 0 4px 0"}),
                    html.P("Last 90 days · sourced from marts.metrics_daily",
                           style={"color": "#64748b", "fontSize": "14px",
                                  "margin": "0 0 24px 0"}),
                    kpi_row([
                        kpi_card("Total GMV", f"${total_gmv:,.0f}",
                                 "gross merchandise value", PRIMARY),
                        kpi_card("Net Revenue", f"${total_net:,.0f}",
                                 "gross minus discounts", ACCENT),
                        kpi_card("Avg Order Value", f"${avg_aov:,.2f}",
                                 "90-day average", PURPLE),
                        kpi_card("Total Units", f"{total_units:,}",
                                 "items sold", WARN),
                    ]),
                    chart_card("GMV vs Net Revenue",
                               "Daily totals across the period", revenue_fig),
                    chart_card("Average Order Value",
                               "Net revenue divided by delivered orders", aov_fig),
                    chart_card("Units Sold",
                               "Total item quantity per day", units_fig),
                ],
                style={"padding": "24px", "maxWidth": "1400px",
                       "margin": "0 auto"},
            ),
        ],
        style=PAGE_STYLE,
    )

    return dash_app