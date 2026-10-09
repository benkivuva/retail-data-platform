"""Shared UI helpers used by every dashboard.

Keeping topbar, KPI cards, and figure styling in one place means adding a
new dashboard is one file, not a copy-paste of layout code.
"""
from __future__ import annotations

import plotly.graph_objects as go
from dash import dcc, html
from flask import has_request_context

PRIMARY = "#0f766e"
ACCENT = "#0ea5e9"
WARN = "#f59e0b"
PURPLE = "#8b5cf6"
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

# Nav entries — add new dashboards here and they appear everywhere.
NAV_ITEMS = [
    ("Operations", "/dashboards/operations/"),
    ("Commercial", "/dashboards/commercial/"),
    ("Finance", "/dashboards/finance/"),
    ("Customers", "/dashboards/customers/"),
]


def current_user_label() -> str:
    """Return 'Name · role' when authenticated, else empty string."""
    if not has_request_context():
        return ""
    try:
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            return f"{current_user.display_name} · {current_user.role}"
    except Exception:
        pass
    return ""


def topbar(current_path: str = "") -> html.Div:
    """Topbar shown at the top of every dashboard page."""
    user_label = current_user_label()

    nav_links = []
    for label, href in NAV_ITEMS:
        is_active = current_path and current_path.startswith(href)
        nav_links.append(
            html.A(
                label,
                href=href,
                style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "padding": "0 12px",
                    "opacity": "1" if is_active else "0.75",
                    "fontWeight": "600" if is_active else "400",
                },
            )
        )

    right = html.Div(
        [
            html.Span(
                user_label,
                style={
                    "fontSize": "13px",
                    "opacity": "0.85",
                    "paddingRight": "16px",
                    "borderRight": "1px solid rgba(255,255,255,0.3)",
                },
            ) if user_label else html.Span(),
            html.A(
                "Logout",
                href="/auth/logout",
                style={
                    "color": "white",
                    "textDecoration": "none",
                    "fontSize": "14px",
                    "paddingLeft": "16px",
                },
            ),
        ],
        style={"display": "flex", "alignItems": "center"},
    )

    return html.Div(
        [
            html.Div(
                "Retail Data Platform",
                style={"fontWeight": "600", "letterSpacing": "0.02em"},
            ),
            html.Div(
                [*nav_links, right],
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


def kpi_card(label: str, value: str, hint: str, accent: str) -> html.Div:
    """KPI card with a colored accent bar."""
    return html.Div(
        [
            html.Div(
                style={
                    "width": "4px",
                    "background": accent,
                    "borderRadius": "4px",
                    "marginRight": "16px",
                    "alignSelf": "stretch",
                }
            ),
            html.Div(
                [
                    html.Div(
                        label,
                        style={
                            "fontSize": "11px",
                            "color": MUTED,
                            "textTransform": "uppercase",
                            "letterSpacing": "0.08em",
                            "fontWeight": "600",
                            "marginBottom": "6px",
                        },
                    ),
                    html.Div(
                        value,
                        style={
                            "fontSize": "32px",
                            "fontWeight": "700",
                            "color": TEXT,
                            "lineHeight": "1.1",
                        },
                    ),
                    html.Div(
                        hint,
                        style={
                            "fontSize": "12px",
                            "color": "#94a3b8",
                            "marginTop": "6px",
                        },
                    ),
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


def chart_card(title: str, subtitle: str, figure: go.Figure) -> html.Div:
    return html.Div(
        [
            html.H3(
                title,
                style={
                    "margin": "0 0 4px 0",
                    "fontSize": "16px",
                    "fontWeight": "600",
                    "color": TEXT,
                },
            ),
            html.P(
                subtitle,
                style={"margin": "0 0 16px 0", "fontSize": "13px", "color": MUTED},
            ),
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


def style_figure(fig: go.Figure) -> go.Figure:
    """Apply the platform's common chart theme."""
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


def kpi_row(cards: list[html.Div]) -> html.Div:
    return html.Div(
        cards,
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(240px, 1fr))",
            "gap": "16px",
            "marginBottom": "24px",
        },
    )