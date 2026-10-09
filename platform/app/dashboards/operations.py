"""Operations dashboard — orders, deliveries, stockouts."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html
from flask import Flask, has_request_context

from ..queries.bigquery import get_daily_metrics

PRIMARY = "#0f766e"
ACCENT = "#0ea5e9"
WARN = "#f59e0b"
TEXT = "#0f172a"
MUTED = "#64748b"

FONT_STACK = "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"

PAGE_STYLE = {
    "fontFamily": FONT_STACK,
    "color": TEXT,
    "background": "#f1f5f9",
    "minHeight": "100vh",
    "padding": "0",
    "margin": "0",
}


def _current_user_label() -> str:
    """Return 'Name · role' when authenticated, else empty.

    Safe to call outside a request context (Dash validates the layout at
    import time, before any request exists).
    """
    if not has_request_context():
        return ""
    try:
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            return f"{current_user.display_name} · {current_user.role}"
    except Exception:
        pass
    return ""


def _topbar() -> html.Div:
    """Topbar shown at the top of every dashboard page."""
    user_label = _current_user_label()

    if user_label:
        right = html.Div(
            [
                html.Span(
                    user_label,
                    style={"fontSize": "13px", "opacity": "0.85",
                           "paddingRight": "16px",
                           "borderRight": "1px solid rgba(255,255,255,0.3)"},
                ),
                html.A(
                    "Logout",
                    href="/auth/logout",
                    style={"color": "white", "textDecoration": "none",
                           "fontSize": "14px", "paddingLeft": "16px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center"},
        )
    else:
        right = html.Div()

    return html.Div(
        [
            html.Div("Retail Data Platform",
                     style={"fontWeight": "600", "letterSpacing": "0.02em"}),
            html.Div(
                [
                    html.A("Operations",
                           href="/dashboards/operations/",
                           style={"color": "white", "textDecoration": "none",
                                  "fontSize": "14px", "paddingRight": "16px"}),
                    right,
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "padding": "0 24px",
            "height": "56px",
            "background": PRIMARY,
            "color": "white",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
        },
    )


def _kpi_card(label: str, value: str, hint: str, accent: str) -> html.Div:
    """KPI card with colored accent bar."""
    return html.Div(
        [
            html.Div(style={"width": "4px", "background": accent,
                            "borderRadius": "4px", "marginRight": "16px",
                            "alignSelf": "stretch"}),
            html.Div(
                [
                    html.Div(label, style={
                        "fontSize": "11px", "color": MUTED,
                        "textTransform": "uppercase", "letterSpacing": "0.08em",
                        "fontWeight": "600", "marginBottom": "6px",
                    }),
                    html.Div(value, style={
                        "fontSize": "32px", "fontWeight": "700",
                        "color": TEXT, "lineHeight": "1.1",
                    }),
                    html.Div(hint, style={
                        "fontSize": "12px", "color": "#94a3b8",
                        "marginTop": "6px",
                    }),
                ],
            ),
        ],
        style={
            "display": "flex",
            "background": "white",
            "borderRadius": "10px",
            "padding": "20px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
            "border": "1px solid #e2e8f0",
        },
    )


def _chart_card(title: str, subtitle: str, figure: go.Figure) -> html.Div:
    return html.Div(
        [
            html.H3(title, style={"margin": "0 0 4px 0", "fontSize": "16px",
                                   "fontWeight": "600", "color": TEXT}),
            html.P(subtitle, style={"margin": "0 0 16px 0", "fontSize": "13px",
                                     "color": MUTED}),
            dcc.Graph(figure=figure, config={"displayModeBar": False}),
        ],
        style={
            "background": "white",
            "borderRadius": "10px",
            "padding": "20px",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
            "border": "1px solid #e2e8f0",
            "marginBottom": "20px",
        },
    )


def _style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family=FONT_STACK, size=12, color="#475569"),
        xaxis=dict(showgrid=False, linecolor="#e2e8f0"),
        yaxis=dict(gridcolor="#f1f5f9", linecolor="#e2e8f0"),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    return fig


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

    total_orders = int(df["total_orders"].sum())
    avg_on_time = float(df["on_time_delivery_rate"].mean())
    avg_delivery = float(df["avg_delivery_minutes"].mean())
    avg_stockouts = float(df["stockout_products"].mean())

    orders_fig = _style_figure(
        px.line(df, x="metric_date", y="total_orders",
                color_discrete_sequence=[PRIMARY])
    )
    orders_fig.update_traces(line=dict(width=2))

    on_time_fig = _style_figure(
        px.line(df, x="metric_date", y="on_time_delivery_rate",
                color_discrete_sequence=[ACCENT])
    )
    on_time_fig.update_traces(line=dict(width=2))
    on_time_fig.update_yaxes(tickformat=".0%", range=[0, 1])

    stockout_fig = _style_figure(
        px.bar(df, x="metric_date", y="stockout_products",
               color_discrete_sequence=[WARN])
    )

    dash_app.layout = html.Div(
        [
            _topbar(),
            html.Div(
                [
                    html.H1("Operations Dashboard",
                            style={"fontSize": "24px", "fontWeight": "700",
                                   "margin": "0 0 4px 0"}),
                    html.P("Last 90 days · sourced from marts.metrics_daily",
                           style={"color": MUTED, "fontSize": "14px",
                                  "margin": "0 0 24px 0"}),
                    html.Div(
                        [
                            _kpi_card("Total Orders", f"{total_orders:,}",
                                      "delivered orders", PRIMARY),
                            _kpi_card("On-Time Rate", f"{avg_on_time:.1%}",
                                      "90-day average", ACCENT),
                            _kpi_card("Avg Delivery", f"{avg_delivery:.0f} min",
                                      "dispatch to delivered", "#8b5cf6"),
                            _kpi_card("Stockouts / Day", f"{avg_stockouts:.1f}",
                                      "products unavailable", WARN),
                        ],
                        style={
                            "display": "grid",
                            "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
                            "gap": "16px",
                            "marginBottom": "24px",
                        },
                    ),
                    _chart_card("Orders per day",
                                "Volume trend across the period", orders_fig),
                    _chart_card("On-time delivery rate",
                                "Share of deliveries arriving by promise time",
                                on_time_fig),
                    _chart_card("Products out of stock",
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