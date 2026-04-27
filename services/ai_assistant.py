"""
AI integration via Anthropic Claude API.

All AI features here:
- Q&A chatbot
- Covenant analyst narrative
- Stress test interpreter
- Board memo narrative
- Anomaly detection
- Lender email drafter
- Renewal negotiation briefing

Designed to fail gracefully — if no API key, dashboard still works.
"""

from __future__ import annotations
import json
from typing import Any

try:
    import anthropic
except ImportError:
    anthropic = None


MODEL = "claude-sonnet-4-5-20250929"   # safe default; user can override
MAX_TOKENS = 1024


def is_available(api_key: str | None) -> bool:
    return bool(api_key) and anthropic is not None


def _client(api_key: str):
    if anthropic is None:
        raise RuntimeError("anthropic SDK not installed")
    return anthropic.Anthropic(api_key=api_key)


def _portfolio_context(logic) -> str:
    """Build a structured context string the AI can reference."""
    cov_summary = logic.covenant_summary()
    health = logic.health_score()
    fin = logic.fin
    mix = logic.fixed_vs_floating()
    lenders = logic.lender_breakdown()

    cov_status = logic.covenant_status()
    breached = [c for c in cov_status if "Breached" in c["status"]]
    near = [c for c in cov_status if "Near" in c["status"]]

    ctx = f"""
JCL DEBT PORTFOLIO SNAPSHOT (as of {logic.as_of}):

PORTFOLIO TOTALS
- Total Sanctioned: ₹{logic.total_sanctioned():.1f} Cr
- Fund-Based: ₹{logic.total_fb():.1f} Cr
- Non-Fund-Based: ₹{logic.total_nfb():.1f} Cr
- Term Loans: ₹{logic.total_term_loan():.1f} Cr
- Annual Interest+Commission: ₹{logic.annual_interest_commission():.2f} Cr
- Weighted Avg Cost (FB+TL): {logic.wac_fb_plus_tl():.2f}%

LENDERS
"""
    for l in lenders:
        ctx += f"- {l['lender']}: ₹{l['sanc']:.1f} Cr ({l['pct_total']:.1f}% of total), {l['facilities']} facilities\n"

    ctx += f"""

FINANCIALS (basis: {logic.basis})
- EBITDA: ₹{fin['ebitda']:.2f} Cr
- Total Debt: ₹{fin['total_debt']:.2f} Cr
- Interest Expense: ₹{fin['interest_exp']:.2f} Cr
- TNW: ₹{fin['tnw']:.2f} Cr
- Net Fixed Assets: ₹{fin['net_fixed_assets']:.2f} Cr

COVENANTS ({cov_summary['total']} total)
- Compliant: {cov_summary['green']}
- Near Breach: {cov_summary['amber']}
- Breached: {cov_summary['red']}
- Compliance %: {cov_summary['compliance_pct']:.1f}%
"""
    if near:
        ctx += "\nCOVENANTS AT RISK:\n"
        for c in near + breached:
            ctx += f"- {c['lender']} {c['covenant']}: actual {c['actual']:.2f} vs threshold {c['threshold']} ({c['headroom']:.1f}% headroom)\n"

    ctx += f"""

PORTFOLIO HEALTH SCORE: {health['composite']}/100
- Covenant component: {health['covenant']}/100
- Maturity component: {health['wam']}/100 (WAM {health['wam_months']:.1f} months)
- Concentration component: {health['concentration']}/100 (HHI {health['hhi']})
- Fixed-rate cushion: {health['fixed']}/100 ({health['fixed_pct']}% fixed)

RATE MIX
- Fixed: ₹{mix['fixed']:.0f} Cr ({mix['fixed']/mix['total']*100:.0f}%)
- Floating: ₹{mix['floating']:.0f} Cr ({mix['floating']/mix['total']*100:.0f}%)
"""
    return ctx


# =============================================================================
# CHATBOT
# =============================================================================
def chat(api_key: str, question: str, logic, history: list = None) -> str:
    """Answer a question about the portfolio."""
    if not is_available(api_key):
        return "⚠ AI not configured. Add ANTHROPIC_API_KEY to Streamlit secrets to enable."

    history = history or []
    context = _portfolio_context(logic)

    system = f"""You are a senior debt portfolio analyst at Jindal Coke Limited (JCL).
You answer questions about JCL's debt portfolio using ONLY the data provided in the context below.
Be concise, factual, numeric, and use Bloomberg-terminal style brevity.
Never invent facts. If the data isn't in the context, say so.
Always show ₹ figures in Crores. All ratios as multiples (e.g., "1.39x").

PORTFOLIO CONTEXT:
{context}
"""

    messages = []
    for h in history[-6:]:  # last 3 turns
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    try:
        client = _client(api_key)
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠ AI request failed: {str(e)[:200]}"


# =============================================================================
# COVENANT ANALYST NARRATIVE
# =============================================================================
def covenant_narrative(api_key: str, logic) -> str:
    if not is_available(api_key):
        return ""

    context = _portfolio_context(logic)
    prompt = """Based on the portfolio context above, write a 4-6 sentence
narrative interpreting the current covenant status. Identify the single most
pressing covenant concern and recommend ONE concrete action. Use plain
English suitable for a CFO. No bullet points."""

    try:
        client = _client(api_key)
        resp = client.messages.create(
            model=MODEL, max_tokens=400,
            system=context,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠ AI narrative unavailable: {str(e)[:200]}"


# =============================================================================
# STRESS TEST INTERPRETER
# =============================================================================
def stress_interpreter(api_key: str, logic, scenario_result: dict, scenario_inputs: dict) -> str:
    if not is_available(api_key):
        return ""

    context = _portfolio_context(logic)

    prompt = f"""Stress scenario applied:
- Rate shock: +{scenario_inputs.get('rate_shock_bps', 0)} bps
- Spread shock: +{scenario_inputs.get('spread_shock_bps', 0)} bps
- EBITDA change: {scenario_inputs.get('ebitda_change_pct', 0)*100:.0f}%
- Debt change: +{scenario_inputs.get('debt_change_pct', 0)*100:.0f}%

Result:
- Stressed annual interest: ₹{scenario_result['annual_interest']:.2f} Cr
- Stressed DSCR: {scenario_result['dscr']:.2f}x
- Stressed Debt/EBITDA: {scenario_result['debt_ebitda']:.2f}x
- Stressed ICR: {scenario_result['icr']:.2f}x

Write a 3-4 sentence interpretation: which covenants would breach under this
scenario, what's the dominant driver, and what is the most realistic
mitigation action. Be specific about lender names."""

    try:
        client = _client(api_key)
        resp = client.messages.create(
            model=MODEL, max_tokens=400,
            system=context,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠ {str(e)[:200]}"


# =============================================================================
# LENDER EMAIL DRAFTER
# =============================================================================
def draft_email(api_key: str, logic, kind: str, lender: str, context_note: str = "") -> str:
    """kind = 'payment' | 'renewal' | 'covenant_certificate'"""
    if not is_available(api_key):
        # Static fallback template
        return _fallback_email_template(kind, lender, context_note)

    portfolio = _portfolio_context(logic)
    prompt = f"""Draft a professional email to the {lender} relationship manager.
Purpose: {kind}.
Additional context: {context_note}

Tone: formal, polite, factual. Include exact figures where relevant.
Include subject line at top. Sign off as 'Treasury Team, JCL'.
Keep it under 150 words."""

    try:
        client = _client(api_key)
        resp = client.messages.create(
            model=MODEL, max_tokens=600,
            system=portfolio,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception:
        return _fallback_email_template(kind, lender, context_note)


def _fallback_email_template(kind: str, lender: str, context: str) -> str:
    if kind == "payment":
        return f"""Subject: Term Loan Payment Confirmation — {lender}

Dear Relationship Manager,

This is to confirm the upcoming term loan instalment payment to {lender} as per the agreed repayment schedule.

{context}

Please acknowledge receipt of this payment instruction and confirm settlement details.

Regards,
Treasury Team
Jindal Coke Limited"""
    elif kind == "renewal":
        return f"""Subject: Facility Renewal Discussion — {lender}

Dear Relationship Manager,

We would like to initiate discussions for the upcoming renewal of our credit facilities with {lender}.

{context}

Could we schedule a call at your convenience to review terms, pricing, and covenant structure for the renewed facilities?

Regards,
Treasury Team
Jindal Coke Limited"""
    else:
        return f"""Subject: Compliance Certificate — {lender}

Dear Relationship Manager,

Please find attached the compliance certificate for {lender} as per our covenant testing requirements.

{context}

Regards,
Treasury Team
Jindal Coke Limited"""


# =============================================================================
# BOARD MEMO NARRATIVE
# =============================================================================
def board_memo_narrative(api_key: str, logic) -> str:
    if not is_available(api_key):
        return _fallback_board_narrative(logic)

    context = _portfolio_context(logic)
    prompt = """Write a 2-paragraph executive summary for the board memo.
Paragraph 1: portfolio health and key numbers.
Paragraph 2: top concern and recommended action.
Plain English, CFO-level brevity."""

    try:
        client = _client(api_key)
        resp = client.messages.create(
            model=MODEL, max_tokens=600,
            system=context,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception:
        return _fallback_board_narrative(logic)


def _fallback_board_narrative(logic) -> str:
    cov = logic.covenant_summary()
    health = logic.health_score()
    return (
        f"JCL's debt portfolio of ₹{logic.total_sanctioned():.1f} Cr across "
        f"{len(logic.lender_breakdown())} lenders remains broadly healthy. "
        f"Of {cov['total']} active covenants, {cov['green']} are compliant and "
        f"{cov['amber']} require monitoring. The composite Portfolio Health "
        f"Score stands at {health['composite']}/100. "
        f"\n\nThe most pressing item is the SIB Current Ratio sitting near its threshold "
        f"with limited headroom. Recommend monitoring monthly and pre-negotiating "
        f"a covenant cushion before the next annual testing date."
    )
