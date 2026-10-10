"""Customers dashboard — segments, acquisition channels, signups."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html
from flask import Flask

from ..queries.bigquery import (
    get_customer_channels,
    get_customer_segments,
    get_customer_signups_by_month,
)
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

URL_BASE = "/dashboards/customers/"

PALETTE = [PRIMARY, ACCENT, PURPLE, WARN, "#ec4899", "#14b8a6"]


def init_customers_dashboard(server: Flask) -> Dash:
    """Mount the customers dashboard on the given Flask app."""
    dash_app = Dash(
        __name__,
        server=server,
        url_base_pathname=URL_BASE,
        title="Customers | Retail Data Platform",
    )

    with server.app_context():
        segments_df = get_customer_segments()
        channels_df = get_customer_channels()
        signups_df = get_customer_signups_by_month()

    total_customers = int(segments_df["customer_count"].sum())
    segment_count = len(segments_df)
    top_segment = segments_df.iloc[0]["segment"] if len(segments_df) else "—"
    top_segment_count = int(segments_df.iloc[0]["customer_count"]) if len(segments_df) else 0
    top_channel = channels_df.iloc[0]["acquisition_channel"] if len(channels_df) else "—"
    top_channel_count = int(channels_df.iloc[0]["customer_count"]) if len(channels_df) else 0

    segment_fig = style_figure(
        px.pie(
            segments_df,
            names="segment",
            values="customer_count",
            color_discrete_sequence=PALETTE,
            hole=0.5,
        )
    )
    segment_fig.update_traces(textinfo="percent+label")

    channel_fig = style_figure(
        px.bar(
            channels_df,
            x="acquisition_channel",
            y="customer_count",
            color_discrete_sequence=[PRIMARY],
            text="customer_count",
        )
    )
    channel_fig.update_traces(textposition="outside")

    signups_fig = style_figure(
        go.Figure(
            go.Scatter(
                x=signups_df["month"],
                y=signups_df["signups"],
                mode="lines+markers",
                line=dict(color=ACCENT, width=2),
                marker=dict(size=6),
                fill="tozeroy",
                fillcolor="rgba(14,165,233,0.12)",
            )
        )
    )

    dash_app.layout = html.Div(
        [
            topbar(current_path=URL_BASE),
            html.Div(
                [
                    html.H1("Customers Dashboard",
                            style={"fontSize": "24px", "fontWeight": "700",
                                   "margin": "0 0 4px 0"}),
                    html.P("Aggregated only · sourced from marts.dim_customers",
                           style={"color": "#64748b", "fontSize": "14px",
                                  "margin": "0 0 24px 0"}),
                    kpi_row([
                        kpi_card("Total Customers", f"{total_customers:,}",
                                 "across all segments", PRIMARY),
                        kpi_card("Segments", f"{segment_count}",
                                 f"top: {top_segment} ({top_segment_count:,})",
                                 PURPLE),
                        kpi_card("Top Channel", top_channel,
                                 f"{top_channel_count:,} customers", ACCENT),
                        kpi_card("Latest Month Signups",
                                 f"{int(signups_df.iloc[-1]['signups']) if len(signups_df) else 0:,}",
                                 "last complete month", WARN),
                    ]),
                    chart_card("Customer segments",
                               "Share of customers by segment", segment_fig),
                    chart_card("Acquisition channels",
                               "How customers found us", channel_fig),
                    chart_card("Signups over time",
                               "Monthly new customer signups, last 24 months",
                               signups_fig),
                ],
                style={"padding": "24px", "maxWidth": "1400px",
                       "margin": "0 auto"},
            ),
        ],
        style=PAGE_STYLE,
    )

    return dash_app