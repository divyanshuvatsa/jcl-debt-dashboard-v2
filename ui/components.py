"""
Reusable UI components — KPI tiles, alert strips, ticker, hero verdict.
All Bloomberg Terminal aesthetic.
"""

import streamlit as st
from .theme import COLORS, status_color


def kpi_tile(label: str, value: str, delta: str = "", delta_dir: str = ""):
    """Render a single KPI tile."""
    delta_class = ""
    if delta:
        if delta_dir == "up":
            delta_class = "kpi-delta-up"
        elif delta_dir == "down":
            delta_class = "kpi-delta-down"

    delta_html = f'<div class="kpi-delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="kpi-tile">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def hero_verdict(status: str, headline: str, body: str):
    """Status: 'good' | 'warn' | 'bad'."""
    status_cls = {"good": "hero-status-good", "warn": "hero-status-warn", "bad": "hero-status-bad"}.get(status, "")
    icon = {"good": "🟢", "warn": "🟡", "bad": "🔴"}.get(status, "")
    st.markdown(f"""
    <div class="hero-verdict {status_cls}">
        <div class="hero-title">PORTFOLIO STATUS</div>
        <div class="hero-headline">{icon} {headline}</div>
        <div class="hero-body">{body}</div>
    </div>
    """, unsafe_allow_html=True)


def alert_strip(message: str, severity: str = "cyan"):
    """severity: 'red' | 'yellow' | 'green' | 'cyan'."""
    cls = f"alert-{severity}"
    st.markdown(f'<div class="alert-strip {cls}">▸ {message}</div>',
                unsafe_allow_html=True)


def terminal_header(text: str):
    st.markdown(f'<div class="terminal-header">▌ {text}</div>',
                unsafe_allow_html=True)


def ticker_strip(items: list[dict]):
    """
    Items: list of {label, value, direction}
    direction: 'up'|'down'|'neutral'
    """
    parts = ['<div class="ticker-strip">']
    parts.append('<span class="live-dot"></span>')
    parts.append(f'<span class="ticker-label">LIVE</span> ')
    for item in items:
        d = item.get("direction", "neutral")
        cls = f"ticker-{d}"
        arrow = "▲" if d == "up" else "▼" if d == "down" else "●"
        parts.append(
            f'<span class="ticker-item">'
            f'<span class="ticker-label">{item["label"]}:</span>'
            f'<span class="{cls}">{arrow} {item["value"]}</span>'
            f'</span>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def section_divider():
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Return HTML span with colored status."""
    color = status_color(status)
    return f'<span style="color:{color}; font-weight:700;">{status}</span>'
