"""
Live data fetchers — FX rates, RBI repo rate, T-Bill yields.
All have graceful fallback so dashboard never breaks if a feed fails.
"""

from __future__ import annotations
import json
import time
from typing import Any

try:
    import requests
except ImportError:
    requests = None


# === Cache to avoid hammering APIs ===
_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 3600  # 1 hour


def _cached(key: str, ttl: int = _TTL_SECONDS):
    """Tiny TTL cache."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            now = time.time()
            if key in _CACHE:
                ts, value = _CACHE[key]
                if now - ts < ttl:
                    return value
            try:
                value = fn(*args, **kwargs)
                _CACHE[key] = (now, value)
                return value
            except Exception:
                # On error, return stale cache or None
                if key in _CACHE:
                    return _CACHE[key][1]
                return None
        return wrapper
    return decorator


# =============================================================================
# FX RATE
# =============================================================================
@_cached("fx_inr")
def fetch_usd_inr() -> dict | None:
    """
    Try multiple free FX endpoints with no API key.
    Returns {"rate": float, "source": str, "timestamp": str} or None.
    """
    if requests is None:
        return None

    endpoints = [
        ("https://api.exchangerate-api.com/v4/latest/USD",
         lambda d: d["rates"]["INR"], "exchangerate-api"),
        ("https://open.er-api.com/v6/latest/USD",
         lambda d: d["rates"]["INR"], "open-er-api"),
    ]
    for url, parser, source in endpoints:
        try:
            r = requests.get(url, timeout=4)
            if r.status_code == 200:
                data = r.json()
                rate = float(parser(data))
                return {"rate": rate, "source": source,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M")}
        except Exception:
            continue
    return None


# =============================================================================
# BENCHMARK RATES (best-effort; many require RBI scraping which is fragile)
# =============================================================================
# These are the fallback values — we expose them via the same interface
# so dashboard can show "live vs hardcoded" status.
FALLBACK_RATES = {
    "REPO":        {"rate": 5.25,  "source": "hardcoded", "as_of": "2026-04"},
    "T_BILL_3M":   {"rate": 5.18,  "source": "hardcoded", "as_of": "2026-04"},
    "TERM_SOFR":   {"rate": 4.30,  "source": "hardcoded", "as_of": "2026-04"},
    "RBL_1Y_MCLR": {"rate": 9.00,  "source": "hardcoded", "as_of": "2026-04"},
    "YBL_3M_MCLR": {"rate": 9.00,  "source": "hardcoded", "as_of": "2026-04"},
    "ICICI_6M_IMCLR": {"rate": 8.30, "source": "hardcoded", "as_of": "2026-04"},
    "SIB_12M_MCLR":   {"rate": 9.75, "source": "hardcoded", "as_of": "2026-04"},
    "BFRR":        {"rate": 8.50, "source": "hardcoded", "as_of": "2026-04"},
}


@_cached("term_sofr")
def fetch_term_sofr() -> dict | None:
    """
    Term SOFR is published daily by CME. The Federal Reserve publishes
    a similar overnight SOFR via FRED. We try a public FRED endpoint.
    Returns None on failure (caller uses fallback).
    """
    if requests is None:
        return None
    try:
        # FRED public CSV for SOFR (no API key needed for small requests)
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SOFR&cosd=" + \
              time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7*86400))
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            lines = [l for l in r.text.strip().split("\n") if l]
            if len(lines) >= 2:
                last_line = lines[-1]
                parts = last_line.split(",")
                if len(parts) == 2 and parts[1] not in ("", "."):
                    return {"rate": float(parts[1]),
                            "source": "FRED",
                            "as_of": parts[0]}
    except Exception:
        pass
    return None


def get_all_rates() -> dict:
    """
    Returns a unified dict {key: {rate, source, as_of}} merging live + fallback.
    """
    rates = dict(FALLBACK_RATES)

    # Try live SOFR
    live_sofr = fetch_term_sofr()
    if live_sofr:
        rates["TERM_SOFR"] = live_sofr

    return rates


def get_fx() -> dict:
    """Returns live or fallback FX rate."""
    live = fetch_usd_inr()
    if live:
        return live
    return {"rate": 86.0, "source": "hardcoded", "timestamp": "2026-04-21"}
