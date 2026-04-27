"""
Dashboard UI — all tabs.

7 Tabs:
1. 📊 OVERVIEW    — hero verdict, KPIs, ticker, alerts, AI narrative
2. 💰 LIQUIDITY   — maturity ladder, TL schedule, repayment forecast
3. 🛡 COVENANTS   — headroom chart, status table, deep dive
4. 🔬 SCENARIOS   — stress sliders, sensitivity matrix, AI interpreter
5. 🤖 ASK AI      — Q&A chatbot
6. 📊 INTELLIGENCE — health score, fixed/float mix, lender risk scorecard
7. 📥 EXPORT      — Board memo, lender one-pagers, certificates, emails
"""

from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from core.financial_logic import FinancialLogic, ScenarioInputs
from services import live_data, ai_assistant, exports
from .components import (
    kpi_tile, hero_verdict, alert_strip, terminal_header,
    ticker_strip, section_divider, status_badge,
)
from .charts import (
    covenant_headroom_chart, lender_donut, maturity_ladder_chart,
    tl_principal_chart, rate_sensitivity_chart, fixed_floating_donut,
    health_gauge, alert_timeline,
)
from .theme import COLORS


class Dashboard:
    def __init__(self, raw_data: dict):
        self.raw = raw_data
        self.logic: FinancialLogic = None  # set after sidebar

    # =========================================================================
    # SIDEBAR
    # =========================================================================
    def render_sidebar(self) -> dict:
        st.sidebar.markdown("## JCL DEBT TERMINAL")
        st.sidebar.markdown("Bloomberg debt monitor v2.0")
        st.sidebar.markdown("---")
        st.sidebar.markdown("**As-of Date**")
        as_of = st.sidebar.date_input("date", value=date(2026, 4, 27), label_visibility="collapsed")
        st.sidebar.markdown("---")
        fx_data = live_data.get_fx()
        st.sidebar.markdown(f"**USD/INR:** {fx_data['rate']:.2f}")
        fx_override = st.sidebar.number_input("FX override", value=float(fx_data["rate"]), min_value=70.0, max_value=120.0, step=0.5, label_visibility="collapsed")
        st.sidebar.markdown("---")
        basis = st.sidebar.radio("**Financial Basis**", options=["FY26E", "FY24A"])
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Quick Scenarios**")
        if st.sidebar.button("+100 bps Rate Shock", use_container_width=True, key="qs1"):
            st.session_state["scenario"] = ScenarioInputs(rate_shock_bps=100)
        if st.sidebar.button("Severe Stress", use_container_width=True, key="qs2"):
            st.session_state["scenario"] = ScenarioInputs(rate_shock_bps=200, ebitda_change_pct=-0.30, debt_change_pct=0.25)
        if st.sidebar.button("EBITDA -20%", use_container_width=True, key="qs3"):
            st.session_state["scenario"] = ScenarioInputs(ebitda_change_pct=-0.20)
        if st.sidebar.button("Reset to Base Case", use_container_width=True, key="qs4"):
            st.session_state["scenario"] = ScenarioInputs()
        st.sidebar.markdown("---")
        api_key = self._get_api_key()
        if api_key and ai_assistant.anthropic is not None:
            st.sidebar.success("AI: Connected")
        else:
            st.sidebar.warning("AI: Add ANTHROPIC_API_KEY in Secrets")
        st.sidebar.markdown("---")
        st.sidebar.markdown("Green = OK | Amber = Watch | Red = Breach")
        st.sidebar.markdown("All figures in Rs. Crores")
        return {"as_of_date": as_of, "fx_rate": fx_override, "basis": basis, "api_key": api_key}

    def _get_api_key(self) -> str | None:
        try:
            return st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            return None

    # =========================================================================
    # HEADER (TICKER STRIP)
    # =========================================================================
    def render_header(self, controls: dict):
        st.markdown(
            f'<h1 style="margin-bottom:0;">JCL DEBT TERMINAL</h1>'
            f'<p style="color:{COLORS["text_dim"]}; margin-top:0; '
            f'font-family:monospace; letter-spacing:2px;">'
            f'JINDAL COKE LIMITED · DEBT PORTFOLIO MONITOR · '
            f'AS OF {controls["as_of_date"].strftime("%d-%b-%Y").upper()}</p>',
            unsafe_allow_html=True
        )

        # Live ticker strip with key metrics
        cov = self.logic.covenant_summary()
        health = self.logic.health_score()
        ticker_items = [
            {"label": "TOTAL", "value": f"₹{self.logic.total_sanctioned():.0f}Cr", "direction": "neutral"},
            {"label": "WAC", "value": f"{self.logic.wac_fb_plus_tl():.2f}%", "direction": "neutral"},
            {"label": "ANNUAL", "value": f"₹{self.logic.annual_interest_commission():.1f}Cr", "direction": "neutral"},
            {"label": "HEALTH", "value": f"{health['composite']}/100",
             "direction": "up" if health["composite"] >= 70 else "down"},
            {"label": "COMPLIANT", "value": f"{cov['green']}/{cov['total']}",
             "direction": "up" if cov["red"] == 0 else "down"},
            {"label": "USD/INR", "value": f"{controls['fx_rate']:.2f}", "direction": "neutral"},
        ]
        ticker_strip(ticker_items)

    # =========================================================================
    # TAB 1: OVERVIEW
    # =========================================================================
    def tab_overview(self, controls: dict):
        cov = self.logic.covenant_summary()
        health = self.logic.health_score()

        # Hero verdict
        if cov["red"] > 0:
            status = "bad"
            headline = f"ACTION REQUIRED: {cov['red']} COVENANT(S) BREACHED"
        elif cov["amber"] > 0:
            status = "warn"
            headline = f"MONITOR: {cov['amber']} COVENANT(S) NEAR BREACH"
        else:
            status = "good"
            headline = "PORTFOLIO HEALTHY — ALL COVENANTS COMPLIANT"

        body = (
            f"Total debt of ₹{self.logic.total_sanctioned():.0f} Cr across "
            f"{len(self.logic.lender_breakdown())} lenders. "
            f"Annual cost ₹{self.logic.annual_interest_commission():.1f} Cr at "
            f"weighted avg {self.logic.wac_fb_plus_tl():.2f}%. "
            f"Health score {health['composite']}/100."
        )
        hero_verdict(status, headline, body)

        # KPI Grid
        terminal_header("KEY METRICS")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_tile("TOTAL SANCTIONED", f"₹{self.logic.total_sanctioned():.0f} Cr",
                     f"{len(self.logic.facilities)} facilities")
        with c2:
            kpi_tile("ANNUAL COST", f"₹{self.logic.annual_interest_commission():.1f} Cr",
                     f"WAC {self.logic.wac_fb_plus_tl():.2f}%")
        with c3:
            kpi_tile("COMPLIANCE", f"{cov['compliance_pct']:.1f}%",
                     f"{cov['green']}/{cov['total']} green",
                     "up" if cov['red'] == 0 else "down")
        with c4:
            kpi_tile("HEALTH SCORE", f"{health['composite']}/100",
                     f"WAM {health['wam_months']:.0f}mo",
                     "up" if health['composite'] >= 70 else "down")

        section_divider()

        # Two-column: gauge + lender donut
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.plotly_chart(health_gauge(health["composite"]),
                            use_container_width=True, key="ov_gauge")
        with col_right:
            st.plotly_chart(lender_donut(self.logic.lender_breakdown()),
                            use_container_width=True, key="ov_donut")

        section_divider()

        # ALERTS
        terminal_header("ALERTS — NEXT 180 DAYS")
        alerts = self.logic.upcoming_alerts(horizon_days=180)
        if not alerts:
            alert_strip("No active alerts — portfolio is in steady state.", "green")
        else:
            for a in alerts[:8]:
                alert_strip(a["message"], a["severity"])

        section_divider()

        # AI NARRATIVE
        terminal_header("AI ANALYST COMMENTARY")
        if controls.get("api_key"):
            cache_key = f"ai_narrative_{controls['as_of_date']}_{controls['basis']}"
            if cache_key not in st.session_state:
                with st.spinner("Generating AI commentary..."):
                    st.session_state[cache_key] = ai_assistant.covenant_narrative(
                        controls["api_key"], self.logic
                    )
            narrative = st.session_state[cache_key]
            st.markdown(f"""
            <div class="chat-msg-ai">
                {narrative}
            </div>
            """, unsafe_allow_html=True)

            if st.button("🔄 Regenerate AI Commentary", key="regen_ov"):
                del st.session_state[cache_key]
                st.rerun()
        else:
            st.info("Add ANTHROPIC_API_KEY in `.streamlit/secrets.toml` to enable AI commentary.")

    # =========================================================================
    # TAB 2: LIQUIDITY
    # =========================================================================
    def tab_liquidity(self, controls: dict):
        terminal_header("DEBT MATURITY PROFILE")

        # Top metrics
        wam = self.logic.weighted_avg_maturity_months()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_tile("WAM", f"{wam:.1f} mo", "Weighted avg maturity")
        with c2:
            tl_principal = sum(tl["principal_outstanding"] for tl in self.logic.tl_schedule)
            kpi_tile("TL OUTSTANDING", f"₹{tl_principal:.0f} Cr", "All term loans")
        with c3:
            next_4q = self.logic._tl_principal_next_12m()
            kpi_tile("PRINCIPAL DUE 12M", f"₹{next_4q:.1f} Cr", "Next 4 quarters")
        with c4:
            renewals_180d = sum(1 for f in self.logic.facilities
                                if isinstance(f.get("maturity"), date)
                                and 0 <= (f["maturity"] - controls["as_of_date"]).days <= 180)
            kpi_tile("RENEWALS 180D", f"{renewals_180d}", "Facilities expiring")

        section_divider()

        # Maturity ladder
        col_l, col_r = st.columns(2)
        with col_l:
            ladder = self.logic.maturity_ladder()
            st.plotly_chart(maturity_ladder_chart(ladder),
                            use_container_width=True, key="liq_ladder")
        with col_r:
            tl_rows = self.logic.tl_principal_by_fy()
            st.plotly_chart(tl_principal_chart(tl_rows),
                            use_container_width=True, key="liq_tl")

        # TL Schedule details
        terminal_header("ACTIVE TERM LOANS")
        for tl in self.logic.tl_schedule:
            with st.expander(f"📌 {tl['lender']} — {tl['facility']} (₹{tl['sanction']} Cr)"):
                cc1, cc2, cc3, cc4 = st.columns(4)
                cc1.metric("Sanction", f"₹{tl['sanction']:.1f} Cr")
                cc2.metric("Outstanding", f"₹{tl['principal_outstanding']:.1f} Cr")
                cc3.metric("Rate", f"{tl['rate']:.2f}%")
                cc4.metric("Qtr Inst", f"₹{tl['qtr_inst']:.2f} Cr")

                cc5, cc6, cc7, cc8 = st.columns(4)
                cc5.metric("Drawdown", tl["drawdown"].strftime("%d-%b-%Y") if hasattr(tl["drawdown"], "strftime") else "—")
                cc6.metric("Rep. Start", tl["rep_start"].strftime("%d-%b-%Y") if hasattr(tl["rep_start"], "strftime") else "—")
                cc7.metric("Maturity", tl["maturity"].strftime("%d-%b-%Y") if hasattr(tl["maturity"], "strftime") else "—")
                cc8.metric("Instalments", f"{tl['num_inst']} qtrly")

        # Renewal calendar
        section_divider()
        terminal_header("RENEWAL CALENDAR (NEXT 365 DAYS)")
        renewals = []
        for f in self.logic.facilities:
            mat = f.get("maturity")
            if isinstance(mat, date):
                days = (mat - controls["as_of_date"]).days
                if 0 <= days <= 365:
                    renewals.append({
                        "Lender": f["lender"],
                        "Facility": f["facility"],
                        "Sanction (₹ Cr)": f["sanc_inr"],
                        "Maturity": mat.strftime("%d-%b-%Y"),
                        "Days Away": days,
                    })
        if renewals:
            df = pd.DataFrame(renewals).sort_values("Days Away")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            alert_strip("No renewals in next 365 days.", "green")

    # =========================================================================
    # TAB 3: COVENANTS
    # =========================================================================
    def tab_covenants(self, controls: dict):
        cov_summary = self.logic.covenant_summary()

        # Summary tiles
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_tile("TOTAL", f"{cov_summary['total']}", "Covenants tracked")
        with c2:
            kpi_tile("COMPLIANT", f"🟢 {cov_summary['green']}",
                     f"{cov_summary['compliance_pct']:.1f}%")
        with c3:
            kpi_tile("NEAR BREACH", f"🟡 {cov_summary['amber']}", "Within 10%")
        with c4:
            kpi_tile("BREACHED", f"🔴 {cov_summary['red']}", "Action required")

        section_divider()

        # Headroom chart
        all_covs = self.logic.covenant_status()
        st.plotly_chart(covenant_headroom_chart(all_covs),
                        use_container_width=True, key="cov_headroom")

        section_divider()

        # Filter controls
        terminal_header("COVENANT DETAIL")
        ccol1, ccol2 = st.columns([1, 3])
        with ccol1:
            lender_filter = st.selectbox(
                "Lender filter",
                ["All"] + sorted(set(c["lender"] for c in all_covs)),
                key="cov_lender_filter"
            )

        # Build display table
        rows = []
        for c in all_covs:
            if lender_filter != "All" and c["lender"] != lender_filter:
                continue
            actual = c["actual"]
            actual_str = f"{actual:.2f}" if isinstance(actual, (int, float)) else str(actual)
            headroom = c["headroom"]
            headroom_str = f"{headroom:.1f}%" if isinstance(headroom, (int, float)) else str(headroom)
            rows.append({
                "Lender":    c["lender"],
                "Covenant":  c["covenant"],
                "Threshold": f"{c['op']}{c['threshold']}",
                "Actual":    actual_str,
                "Headroom":  headroom_str,
                "Status":    c["status"],
                "Frequency": c["freq"],
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Formula explainer
        with st.expander("📖 Covenant Formula Reference"):
            for c in all_covs[:1]:  # show first 5 unique
                pass
            unique = {}
            for c in all_covs:
                key = c["covenant"]
                if key not in unique:
                    unique[key] = c["formula"]
            for name, formula in unique.items():
                st.markdown(f"**{name}**: `{formula}`")

    # =========================================================================
    # TAB 4: SCENARIOS
    # =========================================================================
    def tab_scenarios(self, controls: dict):
        terminal_header("STRESS TEST CONFIGURATION")

        scenario = st.session_state.get("scenario", ScenarioInputs())

        c1, c2, c3 = st.columns(3)
        with c1:
            rate_shock = st.slider("Rate Shock (bps)", -100, 400,
                                   int(scenario.rate_shock_bps), step=25)
        with c2:
            ebitda_change = st.slider("EBITDA Change (%)", -50, 50,
                                      int(scenario.ebitda_change_pct * 100), step=5)
        with c3:
            debt_change = st.slider("Debt Change (%)", -25, 50,
                                    int(scenario.debt_change_pct * 100), step=5)

        c4, c5 = st.columns(2)
        with c4:
            spread_shock = st.slider("Spread Shock (bps)", 0, 200, 0, step=25)
        with c5:
            apply_to_fixed = st.checkbox(
                "Apply rate shock to fixed-rate facilities (less realistic)",
                value=False,
                help="By default fixed-rate facilities are exempt — they don't reprice"
            )

        # Update scenario
        scenario = ScenarioInputs(
            rate_shock_bps=rate_shock,
            spread_shock_bps=spread_shock,
            ebitda_change_pct=ebitda_change / 100,
            debt_change_pct=debt_change / 100,
            apply_to_fixed=apply_to_fixed,
        )
        st.session_state["scenario"] = scenario

        # Compute results
        result = self.logic.apply_scenario(scenario)

        section_divider()
        terminal_header("STRESSED METRICS")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_tile("STRESSED INTEREST", f"₹{result['annual_interest']:.1f} Cr",
                     f"vs ₹{self.logic.annual_interest_commission():.1f} base")
        with c2:
            kpi_tile("DSCR", f"{result['dscr']:.2f}x",
                     "🔴 Breach" if result['dscr'] < 1.20 else "🟢 OK",
                     "down" if result['dscr'] < 1.20 else "up")
        with c3:
            kpi_tile("DEBT/EBITDA", f"{result['debt_ebitda']:.2f}x",
                     "🔴 Breach" if result['debt_ebitda'] > 4.0 else "🟢 OK",
                     "down" if result['debt_ebitda'] > 4.0 else "up")
        with c4:
            kpi_tile("ICR", f"{result['icr']:.2f}x",
                     "🔴 Breach" if result['icr'] < 3.0 else "🟢 OK",
                     "down" if result['icr'] < 3.0 else "up")

        if result.get("excluded_fixed"):
            alert_strip(
                f"₹{result['excluded_fixed']:.0f} Cr excluded from rate shock "
                f"(fixed-rate facilities don't reprice)",
                "cyan"
            )

        section_divider()

        # Sensitivity matrix
        terminal_header("RATE SHOCK SENSITIVITY MATRIX")
        sensitivity = self.logic.rate_sensitivity(max_bps=300, step=25)
        st.plotly_chart(rate_sensitivity_chart(sensitivity),
                        use_container_width=True, key="scn_sens")

        # Sensitivity table
        with st.expander("📊 Sensitivity Table"):
            df = pd.DataFrame(sensitivity)
            df["DSCR"] = df["dscr"].apply(lambda x: f"{x:.2f}x")
            df["Debt/EBITDA"] = df["debt_ebitda"].apply(lambda x: f"{x:.2f}x")
            df["ICR"] = df["icr"].apply(lambda x: f"{x:.2f}x")
            df["Interest"] = df["interest"].apply(lambda x: f"₹{x:.2f} Cr")
            df["Shock"] = df["shock_bps"].apply(lambda x: f"+{x} bps")
            st.dataframe(df[["Shock", "Interest", "DSCR", "Debt/EBITDA", "ICR"]],
                         use_container_width=True, hide_index=True)

        section_divider()

        # Breach threshold finder
        terminal_header("BREACH THRESHOLD ANALYSIS")
        bp1 = self.logic.find_breach_threshold(1.20, ">")
        bp2 = self.logic.find_breach_threshold(1.25, ">")
        c1, c2 = st.columns(2)
        with c1:
            if bp1 > 0:
                alert_strip(
                    f"DSCR breaches 1.20x (YBL/Bajaj/ICICI threshold) at +{bp1} bps rate shock",
                    "yellow"
                )
            else:
                alert_strip("DSCR holds above 1.20x even at +400 bps", "green")
        with c2:
            if bp2 > 0:
                alert_strip(
                    f"DSCR breaches 1.25x (RBL/ICICI threshold) at +{bp2} bps rate shock",
                    "yellow"
                )
            else:
                alert_strip("DSCR holds above 1.25x even at +400 bps", "green")

        section_divider()

        # AI interpreter
        terminal_header("AI STRESS INTERPRETATION")
        if controls.get("api_key"):
            if st.button("🤖 Generate AI Interpretation", key="ai_stress"):
                with st.spinner("Analyzing stress scenario..."):
                    interp = ai_assistant.stress_interpreter(
                        controls["api_key"], self.logic, result,
                        {
                            "rate_shock_bps": rate_shock,
                            "spread_shock_bps": spread_shock,
                            "ebitda_change_pct": ebitda_change / 100,
                            "debt_change_pct": debt_change / 100,
                        }
                    )
                    st.markdown(f'<div class="chat-msg-ai">{interp}</div>',
                                unsafe_allow_html=True)
        else:
            st.info("Configure ANTHROPIC_API_KEY for AI scenario interpretation.")

    # =========================================================================
    # TAB 5: ASK AI
    # =========================================================================
    def tab_ai_chat(self, controls: dict):
        terminal_header("AI PORTFOLIO ANALYST")

        api_key = controls.get("api_key")
        if not api_key:
            st.error("⚠ AI not configured. Add ANTHROPIC_API_KEY to `.streamlit/secrets.toml`.")
            with st.expander("📋 Setup instructions"):
                st.code("""
# 1. Create .streamlit/secrets.toml in your project root
# 2. Add this line:
ANTHROPIC_API_KEY = "sk-ant-..."

# 3. Restart Streamlit
""")
            return

        st.markdown(
            f'<div style="color:{COLORS["text_dim"]}; font-size:0.85rem; margin-bottom:12px;">'
            f'Ask anything about your debt portfolio. The AI has access to all '
            f'34 facilities, 24 covenants, financials, and stress test data.'
            f'</div>',
            unsafe_allow_html=True
        )

        # Suggested questions
        st.markdown("**💡 Try asking:**")
        suggestions = [
            "What's our biggest covenant risk right now?",
            "Which lender has the tightest covenant?",
            "What happens if RBI hikes rates 50 bps?",
            "When is our next term loan payment?",
            "How concentrated is our lender exposure?",
        ]
        cols = st.columns(len(suggestions))
        for i, q in enumerate(suggestions):
            if cols[i].button(q, key=f"sg_{i}", use_container_width=True):
                st.session_state["pending_question"] = q

        # Chat history
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # Render history
        for msg in st.session_state["chat_history"]:
            cls = "chat-msg-user" if msg["role"] == "user" else "chat-msg-ai"
            label = "👤 YOU" if msg["role"] == "user" else "🤖 AI"
            st.markdown(
                f'<div class="{cls}"><b>{label}:</b><br>{msg["content"]}</div>',
                unsafe_allow_html=True
            )

        # Input
        question = st.chat_input("Ask about your portfolio...")
        if st.session_state.get("pending_question"):
            question = st.session_state.pop("pending_question")

        if question:
            st.session_state["chat_history"].append({"role": "user", "content": question})
            with st.spinner("Analyzing..."):
                answer = ai_assistant.chat(
                    api_key, question, self.logic,
                    history=st.session_state["chat_history"]
                )
            st.session_state["chat_history"].append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state["chat_history"]:
            if st.button("🗑 Clear chat history"):
                st.session_state["chat_history"] = []
                st.rerun()

    # =========================================================================
    # TAB 6: INTELLIGENCE
    # =========================================================================
    def tab_intelligence(self, controls: dict):
        health = self.logic.health_score()
        terminal_header("PORTFOLIO HEALTH BREAKDOWN")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            kpi_tile("COVENANT", f"{health['covenant']}/100",
                     "Compliance score", "up" if health['covenant'] >= 70 else "down")
        with c2:
            kpi_tile("MATURITY", f"{health['wam']}/100",
                     f"WAM {health['wam_months']:.0f} mo")
        with c3:
            kpi_tile("CONCENTRATION", f"{health['concentration']}/100",
                     f"HHI {health['hhi']}")
        with c4:
            kpi_tile("RATE FIX %", f"{health['fixed']}/100",
                     f"{health['fixed_pct']}% fixed")

        section_divider()

        # Fixed/Floating + Lender breakdown
        col_l, col_r = st.columns(2)
        with col_l:
            mix = self.logic.fixed_vs_floating()
            st.plotly_chart(fixed_floating_donut(mix),
                            use_container_width=True, key="int_mix")
        with col_r:
            st.plotly_chart(lender_donut(self.logic.lender_breakdown()),
                            use_container_width=True, key="int_donut")

        section_divider()

        # Lender risk scorecard
        terminal_header("LENDER RISK SCORECARD")
        scorecard_data = []
        all_covs = self.logic.covenant_status()
        for l in self.logic.lender_breakdown():
            lender_covs = [c for c in all_covs if c["lender"] == l["lender"]]
            tightest = min(
                [c["headroom"] for c in lender_covs
                 if isinstance(c["headroom"], (int, float))],
                default=999
            )
            cap = l.get("cap")
            scorecard_data.append({
                "Lender":            l["lender"],
                "Sanctioned (₹ Cr)": f"{l['sanc']:.1f}",
                "% of Total":        f"{l['pct_total']:.1f}%",
                "Cap (₹ Cr)":        f"{cap}" if cap else "—",
                "Facilities":        l["facilities"],
                "Tightest Covenant": f"{tightest:.1f}%" if tightest != 999 else "—",
                "Concentration":     "🔴 High" if l["pct_total"] > 35 else
                                     "🟡 Medium" if l["pct_total"] > 20 else "🟢 Low",
            })
        df = pd.DataFrame(scorecard_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        section_divider()

        # Data Quality
        terminal_header("DATA QUALITY")
        dq = self.logic.data_quality_score()
        c1, c2, c3 = st.columns(3)
        c1.metric("Confirmed rates", f"{dq['confirmed']}/{dq['total']}")
        c2.metric("Estimated rates", dq["estimate"])
        c3.metric("Data quality %", f"{dq['pct']}%")

        # List facilities with non-confirmed rates
        non_confirmed = [
            f for f in self.logic.facilities
            if "confirmed" not in str(f.get("rate_status", "")).lower()
        ]
        if non_confirmed:
            with st.expander(f"⚠ {len(non_confirmed)} facilities with estimated/missing rates"):
                df = pd.DataFrame([
                    {
                        "Lender": f["lender"],
                        "Facility": f["facility"],
                        "Sanctioned (₹ Cr)": f["sanc_inr"],
                        "Effective Rate": f"{f['eff_rate']:.2f}%",
                        "Status": f.get("rate_status", "Unknown"),
                    }
                    for f in non_confirmed
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 7: EXPORT
    # =========================================================================
    def tab_export(self, controls: dict):
        terminal_header("BOARD MEMO & DOCUMENTS")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📄 Board Memorandum**")
            st.caption("2-page CFO-level summary with AI narrative")
            if st.button("Generate Board Memo", key="gen_memo"):
                ai_text = ""
                if controls.get("api_key"):
                    with st.spinner("Generating AI narrative..."):
                        ai_text = ai_assistant.board_memo_narrative(
                            controls["api_key"], self.logic
                        )
                with st.spinner("Building document..."):
                    docx_bytes = exports.build_board_memo(self.logic, ai_text)
                st.download_button(
                    "⬇ Download Board Memo (.docx)",
                    docx_bytes,
                    file_name=f"JCL_Board_Memo_{controls['as_of_date']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

        with c2:
            st.markdown("**📋 Lender One-Pager**")
            st.caption("Per-lender facility + covenant summary")
            lender = st.selectbox("Select lender",
                                  sorted(set(f["lender"] for f in self.logic.facilities)),
                                  key="exp_lender")
            if st.button("Generate One-Pager", key="gen_op"):
                with st.spinner("Building..."):
                    docx_bytes = exports.build_lender_onepager(self.logic, lender)
                st.download_button(
                    f"⬇ Download {lender} One-Pager",
                    docx_bytes,
                    file_name=f"JCL_{lender.replace(' ', '_')}_OnePager.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

        section_divider()

        # Compliance certificates
        terminal_header("COMPLIANCE CERTIFICATES")
        c1, c2 = st.columns(2)
        with c1:
            cert_lender = st.selectbox(
                "Lender for certificate",
                sorted(set(f["lender"] for f in self.logic.facilities)),
                key="cert_lender"
            )
        with c2:
            st.markdown("&nbsp;")
            if st.button(f"Generate {cert_lender} Certificate", key="gen_cert"):
                docx_bytes = exports.build_compliance_certificate(self.logic, cert_lender)
                st.download_button(
                    f"⬇ Download {cert_lender} Certificate",
                    docx_bytes,
                    file_name=f"JCL_{cert_lender.replace(' ','_')}_Compliance.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

        section_divider()

        # Email drafts
        terminal_header("EMAIL DRAFTS (COPY-PASTE)")
        c1, c2, c3 = st.columns(3)
        with c1:
            email_kind = st.selectbox(
                "Email type",
                ["payment", "renewal", "covenant_certificate"],
                format_func=lambda x: {"payment": "TL Payment", "renewal": "Facility Renewal",
                                       "covenant_certificate": "Compliance Certificate"}[x]
            )
        with c2:
            email_lender = st.selectbox(
                "Lender",
                sorted(set(f["lender"] for f in self.logic.facilities)),
                key="email_lender"
            )
        with c3:
            st.markdown("&nbsp;")
            gen_email = st.button("✉ Generate Email Draft", key="gen_email")

        if gen_email:
            # Auto-generate context note
            context_note = ""
            if email_kind == "payment":
                for tl in self.logic.tl_schedule:
                    if tl["lender"] == email_lender:
                        context_note = (
                            f"Quarterly instalment: ₹{tl['qtr_inst']:.2f} Cr principal + "
                            f"interest at {tl['rate']:.2f}%. "
                            f"Maturity: {tl['maturity'].strftime('%d-%b-%Y')}."
                        )
                        break
            elif email_kind == "renewal":
                next_renewal = next(
                    (f for f in self.logic.facilities
                     if f["lender"] == email_lender and isinstance(f.get("maturity"), date)
                     and f["maturity"] >= controls["as_of_date"]),
                    None
                )
                if next_renewal:
                    context_note = (
                        f"Facility {next_renewal['facility']} (₹{next_renewal['sanc_inr']:.0f} Cr) "
                        f"matures {next_renewal['maturity'].strftime('%d-%b-%Y')}."
                    )

            with st.spinner("Drafting email..."):
                draft = ai_assistant.draft_email(
                    controls.get("api_key"), self.logic, email_kind, email_lender, context_note
                )

            st.text_area("Email draft (copy below)", draft, height=300, key="email_draft")
            st.caption("✓ Draft generated — copy-paste into your email client.")

        section_divider()

        # CSV exports
        terminal_header("RAW DATA EXPORTS")
        c1, c2, c3 = st.columns(3)
        with c1:
            df = pd.DataFrame(self.logic.facilities)
            st.download_button("⬇ Facilities CSV", df.to_csv(index=False),
                              "facilities.csv", "text/csv", key="csv1",
                              use_container_width=True)
        with c2:
            df = pd.DataFrame(self.logic.covenant_status())
            st.download_button("⬇ Covenants CSV", df.to_csv(index=False),
                              "covenants.csv", "text/csv", key="csv2",
                              use_container_width=True)
        with c3:
            df = pd.DataFrame(self.logic.lender_breakdown())
            st.download_button("⬇ Lenders CSV", df.to_csv(index=False),
                              "lenders.csv", "text/csv", key="csv3",
                              use_container_width=True)

    # =========================================================================
    # FOOTER
    # =========================================================================
    def render_footer(self, controls: dict):
        now = datetime.now().strftime("%d-%b-%Y %H:%M")
        st.markdown(f"""
        <div style="text-align:center; color:{COLORS['text_muted']};
                    padding:20px 0 10px 0; font-size:0.7rem;
                    border-top:1px solid {COLORS['border']}; margin-top:32px;
                    font-family:monospace;">
            <div>JCL DEBT TERMINAL v2.0 · SNAPSHOT {controls['as_of_date'].strftime('%d-%b-%Y').upper()}
            · RENDERED {now} · FX ₹{controls['fx_rate']:.2f}</div>
            <div style="margin-top:4px; color:{COLORS['text_muted']};">
            INTERNAL USE ONLY · NOT FINANCIAL ADVICE · BLOOMBERG-STYLE TERMINAL
            </div>
        </div>
        """, unsafe_allow_html=True)
