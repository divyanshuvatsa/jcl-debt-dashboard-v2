"""
Plotly chart factories — all Bloomberg-styled.
"""

import plotly.graph_objects as go
import plotly.express as px
from .theme import COLORS, PLOTLY_TEMPLATE


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(**PLOTLY_TEMPLATE["layout"])
    return fig


# =============================================================================
# COVENANT HEADROOM BAR CHART
# =============================================================================
def covenant_headroom_chart(covenants: list) -> go.Figure:
    """Horizontal bars showing actual vs threshold."""
    valid = [c for c in covenants if isinstance(c["actual"], (int, float)) and c["op"] != "rating"]
    valid.sort(key=lambda c: c["headroom"] if isinstance(c["headroom"], (int, float)) else 0)

    labels = [f"{c['lender'][:10]} | {c['covenant'][:25]}" for c in valid]
    headroom = [c["headroom"] if isinstance(c["headroom"], (int, float)) else 0 for c in valid]
    colors = []
    for h in headroom:
        if h < 0:
            colors.append(COLORS["red"])
        elif h < 10:
            colors.append(COLORS["yellow"])
        else:
            colors.append(COLORS["green"])

    fig = go.Figure(go.Bar(
        x=headroom, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(color=COLORS["border"], width=1)),
        text=[f"{h:.1f}%" for h in headroom],
        textposition="outside",
        textfont=dict(color=COLORS["text"], family="monospace"),
        hovertemplate="<b>%{y}</b><br>Headroom: %{x:.2f}%<extra></extra>",
    ))
    fig.add_vline(x=10, line_dash="dash", line_color=COLORS["yellow_dim"],
                  annotation_text="10% Buffer", annotation_position="top")
    fig.add_vline(x=0, line_color=COLORS["red"], line_width=2)
    fig.update_layout(
        title=dict(text="COVENANT HEADROOM (% from threshold)",
                   font=dict(color=COLORS["amber"])),
        height=max(300, len(valid) * 24),
        margin=dict(l=200, r=40, t=60, b=40),
    )
    return _apply_theme(fig)


# =============================================================================
# LENDER CONCENTRATION DONUT
# =============================================================================
def lender_donut(lenders: list) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=[l["lender"] for l in lenders],
        values=[l["sanc"] for l in lenders],
        hole=0.55,
        marker=dict(colors=[COLORS["amber"], COLORS["green"], COLORS["cyan"],
                            COLORS["magenta"], COLORS["yellow"]],
                    line=dict(color=COLORS["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(color=COLORS["text"], family="monospace"),
        hovertemplate="<b>%{label}</b><br>₹%{value:.1f} Cr<br>%{percent}<extra></extra>",
    ))
    total = sum(l["sanc"] for l in lenders)
    fig.add_annotation(
        text=f"<b>₹{total:.0f} Cr</b><br><span style='font-size:11px;color:{COLORS['text_dim']}'>TOTAL</span>",
        showarrow=False, font=dict(color=COLORS["amber"], size=20, family="monospace"),
    )
    fig.update_layout(
        title=dict(text="LENDER CONCENTRATION", font=dict(color=COLORS["amber"])),
        height=400, showlegend=False,
    )
    return _apply_theme(fig)


# =============================================================================
# MATURITY LADDER
# =============================================================================
def maturity_ladder_chart(ladder: list) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=[r["fy"] for r in ladder],
        y=[r["amount"] for r in ladder],
        marker=dict(color=COLORS["amber"], line=dict(color=COLORS["amber_glow"], width=1)),
        text=[f"₹{r['amount']:.0f}" for r in ladder],
        textposition="outside",
        textfont=dict(color=COLORS["text"], family="monospace"),
        hovertemplate="<b>%{x}</b><br>₹%{y:.1f} Cr<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="DEBT MATURITY LADDER (₹ Cr by FY)",
                   font=dict(color=COLORS["amber"])),
        height=350,
    )
    return _apply_theme(fig)


# =============================================================================
# TL PRINCIPAL BY FY
# =============================================================================
def tl_principal_chart(rows: list) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=[r["fy"] for r in rows],
        y=[r["amount"] for r in rows],
        marker=dict(color=COLORS["green"], line=dict(color=COLORS["green_dim"], width=1)),
        text=[f"₹{r['amount']:.0f}" for r in rows],
        textposition="outside",
        textfont=dict(color=COLORS["text"], family="monospace"),
        hovertemplate="<b>%{x}</b><br>Principal: ₹%{y:.1f} Cr<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="TERM LOAN PRINCIPAL REPAYMENT BY FY",
                   font=dict(color=COLORS["amber"])),
        height=350,
    )
    return _apply_theme(fig)


# =============================================================================
# RATE SENSITIVITY MATRIX
# =============================================================================
def rate_sensitivity_chart(rows: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[r["shock_bps"] for r in rows],
        y=[r["dscr"] for r in rows],
        mode="lines+markers",
        name="DSCR",
        line=dict(color=COLORS["amber"], width=2),
        marker=dict(size=6, color=COLORS["amber"]),
    ))
    fig.add_trace(go.Scatter(
        x=[r["shock_bps"] for r in rows],
        y=[r["icr"] for r in rows],
        mode="lines+markers",
        name="ICR",
        line=dict(color=COLORS["cyan"], width=2),
        marker=dict(size=6, color=COLORS["cyan"]),
        yaxis="y2",
    ))
    # DSCR threshold line
    fig.add_hline(y=1.20, line_dash="dash", line_color=COLORS["red"],
                  annotation_text="DSCR Min 1.20x", annotation_position="right")

    fig.update_layout(
        title=dict(text="RATE SHOCK SENSITIVITY (DSCR & ICR)",
                   font=dict(color=COLORS["amber"])),
        xaxis=dict(title="Rate Shock (bps)"),
        yaxis=dict(title="DSCR (x)"),
        yaxis2=dict(title="ICR (x)", overlaying="y", side="right"),
        height=400,
        legend=dict(orientation="h", y=-0.2),
    )
    return _apply_theme(fig)


# =============================================================================
# FIXED VS FLOATING DONUT
# =============================================================================
def fixed_floating_donut(mix: dict) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["Fixed", "Floating"],
        values=[mix["fixed"], mix["floating"]],
        hole=0.6,
        marker=dict(colors=[COLORS["green"], COLORS["yellow"]],
                    line=dict(color=COLORS["bg"], width=2)),
        textinfo="label+percent",
        textfont=dict(color=COLORS["text"], family="monospace"),
    ))
    fig.update_layout(
        title=dict(text="FIXED vs FLOATING RATE MIX",
                   font=dict(color=COLORS["amber"])),
        height=350, showlegend=False,
    )
    return _apply_theme(fig)


# =============================================================================
# COVENANT STATUS GAUGE
# =============================================================================
def health_gauge(score: int) -> go.Figure:
    color = COLORS["green"] if score >= 70 else COLORS["yellow"] if score >= 50 else COLORS["red"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(color=color, size=48, family="monospace")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=COLORS["text_dim"],
                      tickfont=dict(color=COLORS["text_dim"])),
            bar=dict(color=color, thickness=0.4),
            bgcolor=COLORS["bg_panel"],
            borderwidth=1,
            bordercolor=COLORS["border_active"],
            steps=[
                dict(range=[0, 50],   color="rgba(255, 59, 59, 0.18)"),
                dict(range=[50, 70],  color="rgba(255, 217, 61, 0.18)"),
                dict(range=[70, 100], color="rgba(0, 210, 106, 0.18)"),
            ],
            threshold=dict(line=dict(color=COLORS["amber"], width=4),
                           thickness=0.75, value=score),
        ),
        title=dict(text="<b>HEALTH SCORE</b>", font=dict(color=COLORS["amber"])),
    ))
    fig.update_layout(height=300)
    return _apply_theme(fig)


# =============================================================================
# DSCR WATERFALL (stress test)
# =============================================================================
def dscr_waterfall(steps: list) -> go.Figure:
    """steps: list of {name, value, total} where the last is final."""
    fig = go.Figure(go.Waterfall(
        x=[s["name"] for s in steps],
        y=[s["value"] for s in steps],
        measure=["absolute"] + ["relative"] * (len(steps) - 2) + ["total"],
        connector=dict(line=dict(color=COLORS["amber_dim"])),
        increasing=dict(marker=dict(color=COLORS["green"])),
        decreasing=dict(marker=dict(color=COLORS["red"])),
        totals=dict(marker=dict(color=COLORS["amber"])),
        text=[f"{s['value']:.2f}" for s in steps],
        textposition="outside",
        textfont=dict(color=COLORS["text"], family="monospace"),
    ))
    fig.update_layout(
        title=dict(text="DSCR STRESS WATERFALL", font=dict(color=COLORS["amber"])),
        height=400,
    )
    return _apply_theme(fig)


# =============================================================================
# ALERT TIMELINE
# =============================================================================
def alert_timeline(alerts: list) -> go.Figure:
    """Horizontal timeline of upcoming alerts."""
    if not alerts:
        return go.Figure()

    color_map = {"red": COLORS["red"], "yellow": COLORS["yellow"], "cyan": COLORS["cyan"]}
    fig = go.Figure()
    for a in alerts:
        if a["due"] is None:
            continue
        fig.add_trace(go.Scatter(
            x=[a["days"]], y=[a["lender"]],
            mode="markers",
            marker=dict(size=14, color=color_map.get(a["severity"], COLORS["cyan"]),
                        line=dict(color=COLORS["bg"], width=2),
                        symbol="diamond"),
            text=[a["message"]],
            hovertemplate="<b>%{y}</b><br>%{text}<br>%{x} days away<extra></extra>",
            showlegend=False,
        ))
    fig.update_layout(
        title=dict(text="UPCOMING EVENTS TIMELINE (DAYS AWAY)",
                   font=dict(color=COLORS["amber"])),
        xaxis=dict(title="Days Away"),
        height=300,
    )
    return _apply_theme(fig)
