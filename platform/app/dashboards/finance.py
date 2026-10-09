"""Finance dashboard — revenue, discounts, delivery fees, gross margin."""
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

URL_BASE = "/dashboards/finance/"


def init_finance_dashboard(server: Flask) -> Dash:
    """Mount the finance dashboard on the given Flask app."""
    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname=URL_BASE,
        title="Finance | Retail Data Platform",
    )

    with server.app_context():
        df = get_daily_metrics(days=90)

    total_net = float(df["net_revenue"].sum())
    total_discount = float(df["total_discount"].sum())
    total_delivery = float(df["total_delivery_fees"].sum())
    total_margin = float(df["total_gross_margin"].sum())
    margin_pct = total_margin / total_net if total_net else 0.0

    # Revenue composition: net + discounts + delivery fees stacked as
    # a bridge of where the money went / came from.
    composition_fig = go.Figure()
    composition_fig.add_trace(go.Bar(
        x=df["metric_date"], y=df["net_revenue"],
        name="Net Revenue", marker_color=PRIMARY,
    ))
    composition_fig.add_trace(go.Bar(
        x=df["metric_date"], y=df["total_discount"],
        name="Discounts Given", marker_color=WARN,
    ))
    composition_fig.add_trace(go.Bar(
        x=df["metric_date"], y=df["total_delivery_fees"],
        name="Delivery Fees", marker_color=ACCENT,
    ))
    style_figure(composition_fig)
    composition_fig.update_layout(
        barmode="group",
        legend=dict(orientation="h", y=1.1, x=0),
    )

    margin_fig = style_figure(
        px.line(df, x="metric_date", y="total_gross_margin",
                color_discrete_sequence=[PURPLE])
    )
    margin_fig.update_traces(line=dict(width=2))

    fees_fig = style_figure(
        px.area(df, x="metric_date", y="total_delivery_fees",
                color_discrete_sequence=[ACCENT])
    )

    dash_app.layout = html.Div(
        [
            topbar(current_path=URL_BASE),
            html.Div(
                [
                    html.H1("Finance Dashboard",
                            style={"fontSize": "24px", "fontWeight": "700",
                                   "margin": "0 0 4px 0"}),
                    html.P("Last 90 days · sourced from marts.metrics_daily",
                           style={"color": "#64748b", "fontSize": "14px",
                                  "margin": "0 0 24px 0"}),
                    kpi_row([
                        kpi_card("Net Revenue", f"${total_net:,.0f}",
                                 "gross minus discounts", PRIMARY),
                        kpi_card("Total Discounts", f"${total_discount:,.0f}",
                                 "revenue given away", WARN),
                        kpi_card("Delivery Fees", f"${total_delivery:,.0f}",
                                 "collected from customers", ACCENT),
                        kpi_card("Gross Margin", f"${total_margin:,.0f}",
                                 f"{margin_pct:.1%} of net revenue", PURPLE),
                    ]),
                    chart_card("Revenue composition",
                               "Net revenue, discounts, and delivery fees side by side",
                               composition_fig),
                    chart_card("Gross margin trend",
                               "Items subtotal minus items cost, per day", margin_fig),
                    chart_card("Delivery fees collected",
                               "Daily fee revenue, filled area", fees_fig),
                ],
                style={"padding": "24px", "maxWidth": "1400px",
                       "margin": "0 auto"},
            ),
        ],
        style=PAGE_STYLE,
    )

    return dash_app