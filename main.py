"""
JCL Debt Terminal v2 — main entry point.

Run locally:
    streamlit run main.py

Deploy:
    Push to GitHub → Streamlit Cloud auto-deploys.
    Don't forget to add ANTHROPIC_API_KEY in Streamlit Cloud secrets.
"""

import streamlit as st

# Page config MUST be first Streamlit call
st.set_page_config(
    page_title="JCL Debt Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from data.excel_loader import load_data
from core.financial_logic import FinancialLogic
from ui.dashboard import Dashboard
from ui.theme import CUSTOM_CSS


def main():
    # Inject Bloomberg Terminal styling
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Load data — uploaded file (in session) → local Excel → hardcoded fallback
    raw_data = st.session_state.get("uploaded_data") or load_data()

    # Build dashboard instance
    dashboard = Dashboard(raw_data)

    # Sidebar (returns control inputs)
    controls = dashboard.render_sidebar()

    # Build financial logic engine using controls
    dashboard.logic = FinancialLogic(
        facility_master=raw_data["facility_master"],
        covenant_master=raw_data["covenant_master"],
        tl_schedule=raw_data["tl_schedule"],
        financials=raw_data["financials"],
        benchmark_rates=raw_data["benchmark_rates"],
        lender_caps=raw_data["lender_caps"],
        as_of_date=controls["as_of_date"],
        fx_rate=controls["fx_rate"],
        basis=controls["basis"],
    )

    # Header (ticker strip, title)
    dashboard.render_header(controls)

    # Tabs
    tab_names = [
        "📊 OVERVIEW",
        "💰 LIQUIDITY",
        "🛡 COVENANTS",
        "🔬 SCENARIOS",
        "🤖 ASK AI",
        "📊 INTEL",
        "📥 EXPORT",
    ]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        dashboard.tab_overview(controls)
    with tabs[1]:
        dashboard.tab_liquidity(controls)
    with tabs[2]:
        dashboard.tab_covenants(controls)
    with tabs[3]:
        dashboard.tab_scenarios(controls)
    with tabs[4]:
        dashboard.tab_ai_chat(controls)
    with tabs[5]:
        dashboard.tab_intelligence(controls)
    with tabs[6]:
        dashboard.tab_export(controls)

    # Footer
    dashboard.render_footer(controls)


if __name__ == "__main__":
    main()
