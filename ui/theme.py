"""
Bloomberg Terminal aesthetic — amber/green/red on near-black.
All visual styling lives here.
"""

# === COLOR PALETTE ===
COLORS = {
    # Core
    "bg":              "#000000",
    "bg_panel":        "#0A0A0A",
    "bg_panel_2":      "#141414",
    "border":          "#1F1F1F",
    "border_active":   "#FFB000",

    # Bloomberg signature
    "amber":           "#FFB000",   # primary highlight
    "amber_dim":       "#B37D00",
    "amber_glow":      "#FFD24D",
    "green":           "#00D26A",   # compliant / good
    "green_dim":       "#008F47",
    "red":             "#FF3B3B",   # breached / bad
    "red_dim":         "#B81F1F",
    "yellow":          "#FFD93D",   # near-breach / warning
    "yellow_dim":      "#B89C0F",
    "cyan":            "#00E5FF",   # info / neutral highlight
    "magenta":         "#FF00C8",   # accent

    # Text
    "text":            "#E8E8E8",
    "text_dim":        "#A0A0A0",
    "text_muted":      "#666666",
}

# Plotly template
PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": COLORS["bg"],
        "plot_bgcolor":  COLORS["bg_panel"],
        "font": {"color": COLORS["text"], "family": "monospace, Consolas, 'Courier New'"},
        "colorway": [
            COLORS["amber"], COLORS["green"], COLORS["cyan"],
            COLORS["magenta"], COLORS["yellow"], COLORS["red"],
        ],
        "xaxis": {
            "gridcolor": COLORS["border"],
            "zerolinecolor": COLORS["border"],
            "linecolor": COLORS["border_active"],
            "tickfont": {"color": COLORS["text_dim"]},
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "zerolinecolor": COLORS["border"],
            "linecolor": COLORS["border_active"],
            "tickfont": {"color": COLORS["text_dim"]},
        },
        "hoverlabel": {
            "bgcolor": COLORS["bg_panel_2"],
            "bordercolor": COLORS["amber"],
            "font": {"color": COLORS["amber"], "family": "monospace"},
        },
        "legend": {"font": {"color": COLORS["text"]}},
    }
}


CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Share+Tech+Mono&display=swap');

/* === GLOBAL === */
.stApp {{
    background: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'JetBrains Mono', 'Share Tech Mono', monospace;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

/* === SIDEBAR === */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #050505 0%, #0A0A0A 100%);
    border-right: 1px solid {COLORS['amber_dim']};
}}

[data-testid="stSidebar"] * {{
    color: {COLORS['text']} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

[data-testid="stSidebar"] .stButton > button {{
    background: {COLORS['bg_panel']};
    color: {COLORS['amber']};
    border: 1px solid {COLORS['amber_dim']};
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.15s;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
    background: {COLORS['amber']};
    color: {COLORS['bg']};
    box-shadow: 0 0 12px {COLORS['amber']}80;
}}

/* === HEADERS === */
h1, h2, h3, h4, h5, h6 {{
    color: {COLORS['amber']};
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
}}

/* === TICKER STRIP === */
.ticker-strip {{
    background: linear-gradient(90deg, #000 0%, #0A0A0A 50%, #000 100%);
    border-top: 1px solid {COLORS['amber']};
    border-bottom: 1px solid {COLORS['amber']};
    padding: 8px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: {COLORS['amber']};
    overflow: hidden;
    margin: 8px 0 16px 0;
}}

.ticker-item {{
    display: inline-block;
    margin-right: 32px;
}}

.ticker-label {{
    color: {COLORS['text_dim']};
    margin-right: 6px;
}}

.ticker-up {{ color: {COLORS['green']}; }}
.ticker-down {{ color: {COLORS['red']}; }}
.ticker-neutral {{ color: {COLORS['amber']}; }}

/* === HERO VERDICT === */
.hero-verdict {{
    background: linear-gradient(135deg, {COLORS['bg_panel']} 0%, {COLORS['bg_panel_2']} 100%);
    border: 2px solid {COLORS['amber']};
    border-left: 6px solid {COLORS['amber']};
    padding: 24px 32px;
    margin: 16px 0 24px 0;
    box-shadow: 0 0 24px {COLORS['amber']}33, inset 0 0 24px #000;
    position: relative;
    overflow: hidden;
}}

.hero-verdict::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(255, 176, 0, 0.02) 2px,
        rgba(255, 176, 0, 0.02) 4px
    );
    pointer-events: none;
}}

.hero-status-good   {{ border-color: {COLORS['green']}; box-shadow: 0 0 24px {COLORS['green']}40, inset 0 0 24px #000; }}
.hero-status-warn   {{ border-color: {COLORS['yellow']}; box-shadow: 0 0 24px {COLORS['yellow']}40, inset 0 0 24px #000; }}
.hero-status-bad    {{ border-color: {COLORS['red']}; box-shadow: 0 0 24px {COLORS['red']}40, inset 0 0 24px #000; }}

.hero-title {{
    font-size: 0.75rem;
    color: {COLORS['text_dim']};
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 8px;
}}

.hero-headline {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {COLORS['amber']};
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: 'JetBrains Mono', monospace;
}}

.hero-body {{
    font-size: 0.95rem;
    color: {COLORS['text']};
    line-height: 1.6;
}}

/* === KPI TILES === */
.kpi-tile {{
    background: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
    border-left: 3px solid {COLORS['amber']};
    padding: 14px 18px;
    transition: all 0.2s;
    height: 100%;
}}

.kpi-tile:hover {{
    border-left-color: {COLORS['amber_glow']};
    box-shadow: 0 0 16px {COLORS['amber']}30;
}}

.kpi-label {{
    font-size: 0.7rem;
    color: {COLORS['text_dim']};
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
}}

.kpi-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: {COLORS['amber']};
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.1;
}}

.kpi-delta {{
    font-size: 0.75rem;
    margin-top: 4px;
    color: {COLORS['text_dim']};
}}

.kpi-delta-up {{ color: {COLORS['green']}; }}
.kpi-delta-down {{ color: {COLORS['red']}; }}

/* === ALERT BAR === */
.alert-strip {{
    background: {COLORS['bg_panel']};
    border-left: 3px solid {COLORS['amber']};
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
}}

.alert-red    {{ border-left-color: {COLORS['red']};    color: {COLORS['red']}; }}
.alert-yellow {{ border-left-color: {COLORS['yellow']}; color: {COLORS['yellow']}; }}
.alert-green  {{ border-left-color: {COLORS['green']};  color: {COLORS['green']}; }}
.alert-cyan   {{ border-left-color: {COLORS['cyan']};   color: {COLORS['cyan']}; }}

/* === TABS === */
.stTabs [data-baseweb="tab-list"] {{
    background: {COLORS['bg_panel']};
    border-bottom: 1px solid {COLORS['amber_dim']};
    gap: 0;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {COLORS['text_dim']};
    border: none;
    border-bottom: 2px solid transparent;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 10px 18px;
}}

.stTabs [aria-selected="true"] {{
    color: {COLORS['amber']} !important;
    border-bottom: 2px solid {COLORS['amber']} !important;
    background: {COLORS['bg_panel_2']};
}}

/* === BUTTONS === */
.stButton > button {{
    background: {COLORS['bg_panel']};
    color: {COLORS['amber']};
    border: 1px solid {COLORS['amber_dim']};
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    transition: all 0.15s;
}}

.stButton > button:hover {{
    background: {COLORS['amber']};
    color: {COLORS['bg']};
    border-color: {COLORS['amber']};
    box-shadow: 0 0 14px {COLORS['amber']}80;
}}

.stDownloadButton > button {{
    background: {COLORS['bg_panel']};
    color: {COLORS['green']};
    border: 1px solid {COLORS['green_dim']};
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
}}

.stDownloadButton > button:hover {{
    background: {COLORS['green']};
    color: {COLORS['bg']};
    box-shadow: 0 0 14px {COLORS['green']}80;
}}

/* === DATAFRAME === */
[data-testid="stDataFrame"] {{
    background: {COLORS['bg_panel']};
    border: 1px solid {COLORS['border']};
}}

/* === METRICS === */
[data-testid="stMetricValue"] {{
    color: {COLORS['amber']} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

[data-testid="stMetricLabel"] {{
    color: {COLORS['text_dim']} !important;
}}

/* === EXPANDER === */
.streamlit-expanderHeader {{
    background: {COLORS['bg_panel']};
    color: {COLORS['amber']} !important;
    font-family: 'JetBrains Mono', monospace !important;
    border: 1px solid {COLORS['border']};
}}

/* === INPUT FIELDS === */
.stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {{
    background: {COLORS['bg_panel']} !important;
    color: {COLORS['amber']} !important;
    border: 1px solid {COLORS['border']} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: {COLORS['amber']} !important;
    box-shadow: 0 0 8px {COLORS['amber']}40 !important;
}}

/* === SELECTBOX === */
.stSelectbox > div > div {{
    background: {COLORS['bg_panel']} !important;
    color: {COLORS['amber']} !important;
    border: 1px solid {COLORS['border']} !important;
    font-family: 'JetBrains Mono', monospace !important;
}}

/* === CHAT (AI bot) === */
.chat-msg-user {{
    background: {COLORS['bg_panel']};
    border-left: 3px solid {COLORS['cyan']};
    padding: 10px 14px;
    margin: 6px 0;
    color: {COLORS['text']};
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
}}

.chat-msg-ai {{
    background: {COLORS['bg_panel_2']};
    border-left: 3px solid {COLORS['amber']};
    padding: 10px 14px;
    margin: 6px 0;
    color: {COLORS['text']};
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
}}

/* === BLINKING DOT === */
@keyframes blink {{
    0%, 50% {{ opacity: 1; }}
    51%, 100% {{ opacity: 0.3; }}
}}

.live-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    background: {COLORS['green']};
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 1.2s infinite;
    box-shadow: 0 0 8px {COLORS['green']};
}}

/* === SECTION DIVIDER === */
.section-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, {COLORS['amber_dim']}, transparent);
    margin: 24px 0;
}}

/* === TERMINAL HEADER === */
.terminal-header {{
    background: {COLORS['bg_panel']};
    border: 1px solid {COLORS['amber']};
    padding: 6px 12px;
    color: {COLORS['amber']};
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 12px;
    display: inline-block;
}}

/* === SCANLINE EFFECT (subtle) === */
.scanline-bg {{
    position: relative;
}}

/* === HIDE STREAMLIT BRANDING === */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
</style>
"""


def status_color(status: str) -> str:
    """Map covenant status to color."""
    s = (status or "").lower()
    if "compliant" in s or "green" in s:
        return COLORS["green"]
    if "near" in s or "amber" in s or "warn" in s:
        return COLORS["yellow"]
    if "breach" in s or "red" in s:
        return COLORS["red"]
    return COLORS["text_dim"]
