"""
Financial calculation engine.

Single source of truth for: covenant computation, scenario shocks,
sensitivity matrix, refinancing risk, weighted average maturity, etc.

All functions are pure given the inputs — no Streamlit dependencies.
"""

from __future__ import annotations
from datetime import date, timedelta
from dataclasses import dataclass


@dataclass
class ScenarioInputs:
    rate_shock_bps:   float = 0.0       # parallel benchmark shift
    spread_shock_bps: float = 0.0       # additive spread
    util_change_pct:  float = 0.0       # +0.10 = +10% utilisation
    ebitda_change_pct: float = 0.0      # -0.15 = -15% EBITDA
    debt_change_pct:  float = 0.0       # +0.10 = +10% debt
    apply_to_fixed:   bool  = False     # if False, fixed-rate facilities are exempt


class FinancialLogic:
    def __init__(
        self,
        facility_master: list,
        covenant_master: list,
        tl_schedule:     list,
        financials:      dict,
        benchmark_rates: dict,
        lender_caps:     dict,
        as_of_date:      date,
        fx_rate:         float = 86.0,
        basis:           str   = "FY26E",
    ):
        self.facilities      = facility_master
        self.covenants       = covenant_master
        self.tl_schedule     = tl_schedule
        self.financials      = financials
        self.benchmark_rates = benchmark_rates
        self.lender_caps     = lender_caps
        self.as_of           = as_of_date
        self.fx_rate         = fx_rate
        self.basis           = basis

    # ---- Financial inputs ----
    @property
    def fin(self) -> dict:
        return self.financials.get(self.basis, self.financials["FY26E"])

    # =========================================================================
    # PORTFOLIO TOTALS
    # =========================================================================
    def total_sanctioned(self) -> float:
        return sum(f["sanc_inr"] for f in self.facilities)

    def total_fb(self) -> float:
        return sum(f["sanc_inr"] for f in self.facilities
                   if str(f.get("category", "")).startswith("FB"))

    def total_nfb(self) -> float:
        return sum(f["sanc_inr"] for f in self.facilities
                   if str(f.get("category", "")).startswith("NFB"))

    def total_term_loan(self) -> float:
        return sum(f["sanc_inr"] for f in self.facilities
                   if "Term" in str(f.get("category", "")))

    def total_outstanding(self) -> float:
        return sum(f.get("outstanding", 0) or 0 for f in self.facilities)

    # =========================================================================
    # WEIGHTED AVERAGE COST
    # =========================================================================
    def wac_fb_plus_tl(self) -> float:
        """WAC across fund-based + term loans only (excl. NFB commission)."""
        total_amt, total_cost = 0.0, 0.0
        for f in self.facilities:
            cat = str(f.get("category", ""))
            if "FB" in cat or "Term" in cat:
                amt = f["sanc_inr"] or 0
                rate = (f.get("eff_rate") or 0) / 100
                total_amt += amt
                total_cost += amt * rate
        return (total_cost / total_amt * 100) if total_amt else 0.0

    def annual_interest_commission(self) -> float:
        """Total annual cost (interest on FB + commission on NFB)."""
        total = 0.0
        for f in self.facilities:
            amt = (f.get("outstanding") or f.get("sanc_inr") or 0)
            rate = (f.get("eff_rate") or 0) / 100
            total += amt * rate
        return total

    # =========================================================================
    # FIXED VS FLOATING SPLIT
    # =========================================================================
    def fixed_vs_floating(self) -> dict:
        fixed, floating = 0.0, 0.0
        for f in self.facilities:
            rt = str(f.get("rate_type", "")).lower()
            amt = f.get("sanc_inr", 0) or 0
            if "float" in rt:
                floating += amt
            else:
                fixed += amt
        return {"fixed": fixed, "floating": floating, "total": fixed + floating}

    # =========================================================================
    # COVENANT CALCULATIONS
    # =========================================================================
    def compute_covenant_actual(self, covenant: str) -> tuple[float | str, str]:
        """
        Returns (actual_value, formula_description).
        """
        f = self.fin
        ebitda = f["ebitda"]
        debt   = f["total_debt"]
        tnw    = f["tnw"]
        intr   = f["interest_exp"]
        nfa    = f["net_fixed_assets"]
        ca     = f.get("current_assets", 0)
        cl     = f.get("current_liab", 1)
        tax    = f.get("tax_paid", 0)

        # TL principal due in next 12 months
        tl_principal_ttm = self._tl_principal_next_12m()

        c = covenant.lower()

        if "dscr" in c:
            denom = (intr + tl_principal_ttm) or 1
            return ((ebitda - tax) / denom,
                    "(EBITDA − Tax) / (Interest + TL Principal Due 12M)")
        if "term debt" in c:
            tl = self._term_debt_outstanding()
            return (tl / ebitda if ebitda else 0,
                    "Term Debt / EBITDA")
        if "total debt / ebitda" in c or ("debt" in c and "ebitda" in c and "total" in c):
            return (debt / ebitda if ebitda else 0,
                    "Total Debt / EBITDA")
        if "total debt / atnw" in c or "td / atnw" in c:
            return (debt / tnw if tnw else 0, "Total Debt / ATNW")
        if "tol" in c and ("tnw" in c or "atnw" in c):
            tol = debt + cl  # rough proxy
            return (tol / tnw if tnw else 0, "TOL / TNW (proxy)")
        if "facr" in c:
            return (nfa / debt if debt else 0, "Net Fixed Assets / Total Debt")
        if "icr" in c:
            return (ebitda / intr if intr else 0, "EBITDA / Interest Expense")
        if "current ratio" in c:
            return (ca / cl if cl else 0, "Current Assets / Current Liabilities")
        if "debt equity" in c:
            return (debt / tnw if tnw else 0, "Total Debt / TNW")
        if "rating" in c:
            return ("CARE A+; Stable / A1", "External rating from agencies")
        return (0.0, "Unknown covenant")

    def _tl_principal_next_12m(self) -> float:
        """Sum of TL principal due in next 4 quarters."""
        total = 0.0
        for tl in self.tl_schedule:
            if not isinstance(tl.get("rep_start"), date):
                continue
            if self.as_of >= tl["rep_start"] and self.as_of <= tl.get("maturity", date.max):
                # Next 4 quarterly instalments
                total += tl["qtr_inst"] * 4
        return total

    def _term_debt_outstanding(self) -> float:
        return sum(tl.get("principal_outstanding", tl.get("sanction", 0))
                   for tl in self.tl_schedule)

    def covenant_status(self) -> list[dict]:
        """For each covenant, compute actual, status, headroom %."""
        result = []
        for cov in self.covenants:
            actual, formula = self.compute_covenant_actual(cov["covenant"])
            op = cov["op"]
            thr = cov["threshold"]

            if op == "rating":
                status, headroom = "Compliant (Green)", "N/A"
            elif isinstance(actual, str):
                status, headroom = "Pending", "N/A"
            else:
                status, headroom = self._evaluate(op, actual, thr)

            result.append({
                **cov,
                "actual":    actual,
                "formula":   formula,
                "status":    status,
                "headroom":  headroom,
            })
        return result

    @staticmethod
    def _evaluate(op: str, actual: float, threshold: float) -> tuple[str, float]:
        if op in (">", ">="):
            headroom_pct = (actual - threshold) / threshold * 100
            if actual < threshold:
                return ("Breached (Red)", headroom_pct)
            elif headroom_pct < 10:
                return ("Near Breach (Amber)", headroom_pct)
            else:
                return ("Compliant (Green)", headroom_pct)
        else:  # < or <=
            headroom_pct = (threshold - actual) / threshold * 100
            if actual > threshold:
                return ("Breached (Red)", headroom_pct)
            elif headroom_pct < 10:
                return ("Near Breach (Amber)", headroom_pct)
            else:
                return ("Compliant (Green)", headroom_pct)

    def covenant_summary(self) -> dict:
        rows = self.covenant_status()
        green = sum(1 for r in rows if "Compliant" in r["status"])
        amber = sum(1 for r in rows if "Near" in r["status"])
        red   = sum(1 for r in rows if "Breached" in r["status"])
        return {
            "total":  len(rows),
            "green":  green,
            "amber":  amber,
            "red":    red,
            "compliance_pct": green / len(rows) * 100 if rows else 0,
        }

    # =========================================================================
    # SCENARIO ENGINE (with smart fixed-rate exclusion)
    # =========================================================================
    def apply_scenario(self, s: ScenarioInputs) -> dict:
        rate_shock = s.rate_shock_bps / 10000   # 100 bps -> 0.01
        spread_shock = s.spread_shock_bps / 10000
        ebitda_mul = 1 + s.ebitda_change_pct
        debt_mul   = 1 + s.debt_change_pct
        util_mul   = 1 + s.util_change_pct

        # Recompute interest with shock
        new_interest = 0.0
        excluded_amt = 0.0
        for f in self.facilities:
            cat = str(f.get("category", ""))
            if not ("FB" in cat or "Term" in cat):
                continue  # NFB commission lines unaffected
            rate_type = str(f.get("rate_type", "")).lower()
            base_rate = (f.get("eff_rate") or 0) / 100
            amt = (f.get("outstanding") or f.get("sanc_inr") or 0) * util_mul

            if "float" not in rate_type and not s.apply_to_fixed:
                # Fixed: don't reprice
                new_rate = base_rate
                excluded_amt += amt
            else:
                new_rate = base_rate + rate_shock + spread_shock

            new_interest += amt * new_rate

        # Add NFB commission unchanged
        for f in self.facilities:
            cat = str(f.get("category", ""))
            if "NFB" in cat:
                amt = (f.get("outstanding") or f.get("sanc_inr") or 0)
                rate = (f.get("eff_rate") or 0) / 100
                new_interest += amt * rate

        # Adjust EBITDA, debt
        ebitda = self.fin["ebitda"] * ebitda_mul
        debt   = self.fin["total_debt"] * debt_mul
        tax    = self.fin.get("tax_paid", 0)

        # Recompute key ratios
        principal_ttm = self._tl_principal_next_12m()
        dscr = (ebitda - tax) / (new_interest + principal_ttm) if (new_interest + principal_ttm) else 0
        debt_ebitda = debt / ebitda if ebitda else 0
        icr = ebitda / new_interest if new_interest else 0

        return {
            "annual_interest":   new_interest,
            "ebitda_stressed":   ebitda,
            "debt_stressed":     debt,
            "dscr":              dscr,
            "debt_ebitda":       debt_ebitda,
            "icr":               icr,
            "excluded_fixed":    excluded_amt,
        }

    # =========================================================================
    # RATE SENSITIVITY MATRIX
    # =========================================================================
    def rate_sensitivity(self, max_bps: int = 200, step: int = 25) -> list[dict]:
        """For each rate shock from 0 to max_bps, compute DSCR, Debt/EBITDA, ICR."""
        rows = []
        for bps in range(0, max_bps + 1, step):
            scenario = ScenarioInputs(rate_shock_bps=bps)
            r = self.apply_scenario(scenario)
            rows.append({
                "shock_bps":  bps,
                "interest":   r["annual_interest"],
                "dscr":       r["dscr"],
                "debt_ebitda": r["debt_ebitda"],
                "icr":        r["icr"],
            })
        return rows

    def find_breach_threshold(self, covenant_threshold: float, op: str = ">") -> int:
        """Find the rate shock (bps) where DSCR breaches the given threshold."""
        for bps in range(0, 401, 5):
            r = self.apply_scenario(ScenarioInputs(rate_shock_bps=bps))
            if op == ">" and r["dscr"] < covenant_threshold:
                return bps
            if op == "<" and r["debt_ebitda"] > covenant_threshold:
                return bps
        return -1  # never breaches in this range

    # =========================================================================
    # MATURITY / REFINANCING
    # =========================================================================
    def maturity_ladder(self, horizon_years: int = 5) -> list[dict]:
        """Sanctioned amount maturing in each FY going forward."""
        ladder = {}
        for f in self.facilities:
            mat = f.get("maturity")
            if not isinstance(mat, date):
                continue
            fy = mat.year if mat.month <= 3 else mat.year + 1
            label = f"FY{str(fy)[-2:]}"
            ladder[label] = ladder.get(label, 0) + f.get("sanc_inr", 0)

        # Sort and limit
        sorted_keys = sorted(ladder.keys())
        return [{"fy": k, "amount": ladder[k]} for k in sorted_keys[:horizon_years * 2]]

    def tl_principal_by_fy(self) -> list[dict]:
        """TL principal by FY (next 10 years)."""
        from collections import defaultdict
        by_fy = defaultdict(float)
        for tl in self.tl_schedule:
            if not isinstance(tl.get("rep_start"), date):
                continue
            current = tl["rep_start"]
            inst_amt = tl["qtr_inst"]
            num_inst = tl["num_inst"]
            for i in range(num_inst):
                pay_date = current + timedelta(days=i * 91)
                if pay_date > tl.get("maturity", date.max):
                    break
                fy = pay_date.year if pay_date.month <= 3 else pay_date.year + 1
                by_fy[f"FY{str(fy)[-2:]}"] += inst_amt
        return sorted([{"fy": k, "amount": v} for k, v in by_fy.items()],
                      key=lambda x: x["fy"])

    def weighted_avg_maturity_months(self) -> float:
        """WAM in months, weighted by sanctioned amount."""
        total_amt, total_weight = 0.0, 0.0
        for f in self.facilities:
            mat = f.get("maturity")
            if not isinstance(mat, date):
                continue
            months = (mat.year - self.as_of.year) * 12 + (mat.month - self.as_of.month)
            if months < 0:
                continue
            amt = f.get("sanc_inr", 0)
            total_amt += amt
            total_weight += amt * months
        return total_weight / total_amt if total_amt else 0

    # =========================================================================
    # LENDER CONCENTRATION
    # =========================================================================
    def lender_breakdown(self) -> list[dict]:
        from collections import defaultdict
        groups = defaultdict(lambda: {"sanc": 0, "outstanding": 0, "facilities": 0})
        for f in self.facilities:
            l = f["lender"]
            groups[l]["sanc"] += f.get("sanc_inr", 0)
            groups[l]["outstanding"] += f.get("outstanding", 0) or 0
            groups[l]["facilities"] += 1

        total = sum(g["sanc"] for g in groups.values())
        rows = []
        for lender, g in groups.items():
            cap_info = self.lender_caps.get(lender, {})
            rows.append({
                "lender":      lender,
                "sanc":        g["sanc"],
                "outstanding": g["outstanding"],
                "facilities":  g["facilities"],
                "cap":         cap_info.get("cap"),
                "cap_note":    cap_info.get("note", ""),
                "pct_total":   g["sanc"] / total * 100 if total else 0,
            })
        return sorted(rows, key=lambda r: -r["sanc"])

    def herfindahl_index(self) -> float:
        """HHI for lender concentration. <1500 = unconcentrated, >2500 = concentrated."""
        total = self.total_sanctioned()
        rows = self.lender_breakdown()
        return sum(((r["sanc"] / total * 100) ** 2) for r in rows) if total else 0

    # =========================================================================
    # PORTFOLIO HEALTH SCORE  (0-100, weighted composite)
    # =========================================================================
    def health_score(self) -> dict:
        # 1. Covenant compliance (40%)
        cov = self.covenant_summary()
        cov_score = cov["compliance_pct"]

        # 2. WAM (20%) — longer is better, target > 36 months
        wam = self.weighted_avg_maturity_months()
        wam_score = min(100, wam / 36 * 100)

        # 3. Concentration (20%) — lower HHI is better
        hhi = self.herfindahl_index()
        conc_score = max(0, 100 - (hhi - 1000) / 30) if hhi > 1000 else 100

        # 4. Fixed rate cushion (20%) — % of debt fixed-rate
        mix = self.fixed_vs_floating()
        fixed_pct = mix["fixed"] / mix["total"] * 100 if mix["total"] else 0
        fixed_score = min(100, fixed_pct * 1.5)  # cap

        composite = (cov_score * 0.40 + wam_score * 0.20 +
                     conc_score * 0.20 + fixed_score * 0.20)

        return {
            "composite":     round(composite),
            "covenant":      round(cov_score),
            "wam":           round(wam_score),
            "concentration": round(conc_score),
            "fixed":         round(fixed_score),
            "wam_months":    round(wam, 1),
            "hhi":           round(hhi),
            "fixed_pct":     round(fixed_pct, 1),
        }

    # =========================================================================
    # ALERTS / DAYS-TO-ACTION
    # =========================================================================
    def upcoming_alerts(self, horizon_days: int = 180) -> list[dict]:
        alerts = []
        for f in self.facilities:
            mat = f.get("maturity")
            if not isinstance(mat, date):
                continue
            days = (mat - self.as_of).days
            if 0 <= days <= horizon_days:
                severity = "red" if days <= 30 else "yellow" if days <= 90 else "cyan"
                alerts.append({
                    "type":    "Renewal",
                    "lender":  f["lender"],
                    "facility": f["facility"],
                    "due":     mat,
                    "days":    days,
                    "severity": severity,
                    "message": f"{f['lender']} {f['facility']} matures {mat.strftime('%d-%b-%Y')} ({days}d)",
                })

        # TL upcoming payments (next 4 quarters)
        for tl in self.tl_schedule:
            if not isinstance(tl.get("rep_start"), date):
                continue
            current = tl["rep_start"]
            for i in range(tl["num_inst"]):
                pay_date = current + timedelta(days=i * 91)
                if pay_date < self.as_of:
                    continue
                days = (pay_date - self.as_of).days
                if days > horizon_days:
                    break
                severity = "red" if days <= 7 else "yellow" if days <= 30 else "cyan"
                alerts.append({
                    "type":    "TL Payment",
                    "lender":  tl["lender"],
                    "facility": tl["facility"],
                    "due":     pay_date,
                    "days":    days,
                    "severity": severity,
                    "message": (f"{tl['lender']} TL Q-payment ₹{tl['qtr_inst']:.2f} Cr "
                                f"due {pay_date.strftime('%d-%b-%Y')} ({days}d)"),
                })
                break  # only show the next one per TL

        # Covenant near-breach alerts
        for cov in self.covenant_status():
            if "Near" in cov["status"] or "Breached" in cov["status"]:
                sev = "red" if "Breached" in cov["status"] else "yellow"
                alerts.append({
                    "type":     "Covenant",
                    "lender":   cov["lender"],
                    "facility": cov["covenant"],
                    "due":      None,
                    "days":     0,
                    "severity": sev,
                    "message":  (f"{cov['lender']} {cov['covenant']}: "
                                 f"actual {cov['actual']:.2f} vs threshold {cov['threshold']} "
                                 f"({cov['headroom']:.1f}% headroom)"),
                })

        return sorted(alerts, key=lambda a: (a["days"] if a["due"] else -1, a["severity"]))

    # =========================================================================
    # DATA QUALITY
    # =========================================================================
    def data_quality_score(self) -> dict:
        total = len(self.facilities)
        confirmed = sum(1 for f in self.facilities
                        if "confirmed" in str(f.get("rate_status", "")).lower())
        return {
            "total":     total,
            "confirmed": confirmed,
            "estimate":  total - confirmed,
            "pct":       round(confirmed / total * 100, 1) if total else 0,
        }
