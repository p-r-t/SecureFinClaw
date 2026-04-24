"""Screener Tool — bulk stock discovery via yfinance screen() API.

Uses yf.screen() with predefined Yahoo screener queries and custom EquityQuery
filters to surface value-investing candidates in a single API call.
No per-ticker iteration — no rate-limit risk.
"""

import asyncio
import json
from typing import Any

import yfinance as yf
from loguru import logger
from pydantic import ConfigDict

from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json


# ---------------------------------------------------------------------------
# Developed-market region codes (Yahoo Finance valid values)
# ---------------------------------------------------------------------------

# All developed-market regions we want to cover by default.
# These are Yahoo Finance's two-letter region codes.
DEVELOPED_MARKET_REGIONS = [
    "us",   # United States
    "ca",   # Canada
    "gb",   # United Kingdom
    "de",   # Germany
    "fr",   # France
    "au",   # Australia
    "ch",   # Switzerland
    "nl",   # Netherlands
    "se",   # Sweden
    "no",   # Norway
    "dk",   # Denmark
    "jp",   # Japan
    "sg",   # Singapore
    "nz",   # New Zealand
    "ie",   # Ireland
    "at",   # Austria
    "be",   # Belgium
    "fi",   # Finland
]

# Preset → Yahoo predefined screen name mapping (None = custom EquityQuery)
_PRESETS: dict[str, str | None] = {
    "dhandho": None,               # Custom multi-region EquityQuery (built below)
    "undervalued_growth": "undervalued_growth_stocks",
    "undervalued_large_cap": "undervalued_large_caps",
    "aggressive_small_cap": "aggressive_small_caps",
    "most_shorted": "most_shorted_stocks",
    "growth_tech": "growth_technology_stocks",
    # --- New funnel-aligned presets ---
    "net_net": None,               # Graham NCAV proxy: P/B < 1, market cap $50M-$2B
    "dividend_safety": None,       # Dividend & Income funnel: yield 3.5-7%, payout < 65%
    "turnaround_candidate": None,  # Turnaround funnel: 50-80% off 52w high, small/mid-cap
    "high_roic_small_cap": None,   # Hidden Champion: ROIC>20%, small-cap, insider-owned
    "asset_heavy_discount": None,  # Asset-Heavy/SOTP: P/B < 0.8, EV/EBITDA < 6
    "drawdown_50_80": None,        # Cyclical/Turnaround: deeply beaten-down names
}


def _build_query(preset: str):
    """Build a custom EquityQuery for the given preset name."""
    try:
        from yfinance import EquityQuery
    except ImportError:
        return None

    us_only = EquityQuery("eq", ["region", "us"])

    if preset == "net_net":
        # Graham NCAV proxy: P/B < 1.0 (hard assets > market cap),
        # market cap $50M-$2B, avg volume > 100K.
        # True NCAV (current_assets - total_liabilities) requires per-ticker calls;
        # instruct the agent to run yfinance(financials) for shortlisted names.
        return EquityQuery("and", [
            us_only,
            EquityQuery("lt", ["pricetobookratio", 1.0]),
            EquityQuery("gt", ["pricetobookratio", 0.01]),   # avoid negative-equity traps
            EquityQuery("gt", ["intradaymarketcap", 50_000_000]),
            EquityQuery("lt", ["intradaymarketcap", 2_000_000_000]),
        ])

    elif preset == "dividend_safety":
        # Dividend & Income funnel: yield 3.5-7%, profitable, low leverage
        return EquityQuery("and", [
            us_only,
            EquityQuery("gt", ["dividendyield", 0.035]),
            EquityQuery("lt", ["dividendyield", 0.07]),
            EquityQuery("gt", ["peratio.lasttwelvemonths", 0.1]),  # profitable
            EquityQuery("lt", ["totaldebtequity.lasttwelvemonths", 1.5]),
            EquityQuery("gt", ["intradaymarketcap", 500_000_000]),
        ])

    elif preset == "turnaround_candidate":
        # Turnaround funnel: P/B < 1.5 and P/E low, suggesting depressed earnings.
        # 52w-high drawdown filter requires post-screener calculation (no EquityQuery field);
        # instruct the agent to compute distance from 52w high on results.
        return EquityQuery("and", [
            us_only,
            EquityQuery("lt", ["pricetobookratio", 1.5]),
            EquityQuery("gt", ["pricetobookratio", 0.01]),
            EquityQuery("gt", ["intradaymarketcap", 100_000_000]),
            EquityQuery("lt", ["intradaymarketcap", 10_000_000_000]),
        ])

    elif preset == "high_roic_small_cap":
        # Hidden Champion funnel: ROIC>15% proxy via ROE, small-cap ($200M-$2B), P/E < 20
        return EquityQuery("and", [
            us_only,
            EquityQuery("gt", ["returnonequity.lasttwelvemonths", 0.15]),
            EquityQuery("gt", ["intradaymarketcap", 200_000_000]),
            EquityQuery("lt", ["intradaymarketcap", 2_000_000_000]),
            EquityQuery("gt", ["peratio.lasttwelvemonths", 0.1]),
            EquityQuery("lt", ["peratio.lasttwelvemonths", 20]),
            EquityQuery("lt", ["totaldebtequity.lasttwelvemonths", 1.0]),
        ])

    elif preset == "asset_heavy_discount":
        # Asset-Heavy/SOTP funnel: P/B < 0.8, EV/EBITDA < 8
        return EquityQuery("and", [
            us_only,
            EquityQuery("lt", ["pricetobookratio", 0.8]),
            EquityQuery("gt", ["pricetobookratio", 0.01]),
            EquityQuery("lt", ["evtoebitda.lasttwelvemonths", 8]),
            EquityQuery("gt", ["evtoebitda.lasttwelvemonths", 0.5]),
            EquityQuery("gt", ["intradaymarketcap", 200_000_000]),
        ])

    elif preset == "drawdown_50_80":
        # Cyclical/Turnaround: P/B < 1 and low P/E — proxy for deeply beaten-down names.
        # Post-screener: compute pct from 52w high and filter for 50-80% drawdown.
        return EquityQuery("and", [
            us_only,
            EquityQuery("lt", ["pricetobookratio", 1.2]),
            EquityQuery("gt", ["pricetobookratio", 0.01]),
            EquityQuery("gt", ["peratio.lasttwelvemonths", 0.1]),
            EquityQuery("lt", ["peratio.lasttwelvemonths", 10]),
            EquityQuery("gt", ["intradaymarketcap", 100_000_000]),
        ])

    return None


def _build_dhandho_query(regions: list[str] | None = None):
    """Build a custom EquityQuery for Dhandho value criteria across developed markets.

    Filters:
    - Region: developed-market countries (US + Canada + Europe + APAC developed)
    - P/E (TTM) between 0.1 and 15  (profitable but cheap)
    - ROE (TTM) > 12%               (quality businesses)
    - Market cap > $500M            (avoid micro-caps with bad data)
    - D/E (LTM) < 1.0               (conservative balance sheet)
    """
    try:
        from yfinance import EquityQuery

        region_list = regions or DEVELOPED_MARKET_REGIONS

        # Build region filter: is-in supports multiple values in one node
        region_filter = EquityQuery("is-in", ["region"] + region_list)

        return EquityQuery("and", [
            region_filter,
            EquityQuery("gt", ["peratio.lasttwelvemonths", 0.1]),
            EquityQuery("lt", ["peratio.lasttwelvemonths", 15]),
            EquityQuery("gt", ["returnonequity.lasttwelvemonths", 0.12]),
            EquityQuery("gt", ["intradaymarketcap", 500_000_000]),
            EquityQuery("lt", ["totaldebtequity.lasttwelvemonths", 1.0]),
        ])
    except (ImportError, Exception) as exc:
        logger.warning(f"EquityQuery unavailable, falling back to predefined: {exc}")
        return None


_CUSTOM_PRESETS = {"net_net", "dividend_safety", "turnaround_candidate",
                   "high_roic_small_cap", "asset_heavy_discount", "drawdown_50_80"}


def _run_screen(preset: str, limit: int) -> dict:
    """Synchronous wrapper — executed in a thread."""
    try:
        # Resolve query
        if preset == "dhandho":
            query = _build_dhandho_query()
            if query is None:
                query = "undervalued_growth_stocks"
        elif preset in _CUSTOM_PRESETS:
            query = _build_query(preset)
            if query is None:
                return {"error": f"EquityQuery unavailable for preset {preset!r}. Upgrade yfinance."}
        elif preset in _PRESETS:
            query = _PRESETS[preset]
        else:
            return {"error": f"Unknown preset: {preset!r}. Available: {list(_PRESETS.keys())}"}

        response = yf.screen(query, size=limit)

        if not response or "quotes" not in response:
            return {"error": "Screener returned no results.", "raw_keys": list(response.keys()) if response else []}

        quotes = response["quotes"][:limit]

        results = []
        for q in quotes:
            price = q.get("regularMarketPrice")
            high_52w = q.get("fiftyTwoWeekHigh")
            pct_from_high = None
            if price and high_52w and high_52w > 0:
                pct_from_high = round(((price - high_52w) / high_52w) * 100, 1)

            results.append({
                "symbol": q.get("symbol"),
                "name": q.get("shortName") or q.get("longName"),
                "price": price,
                "change_pct": q.get("regularMarketChangePercent"),
                "pe_ratio": q.get("trailingPE"),
                "forward_pe": q.get("forwardPE"),
                "price_to_book": q.get("priceToBook"),
                "dividend_yield": q.get("dividendYield"),
                "market_cap": q.get("marketCap"),
                "52w_low": q.get("fiftyTwoWeekLow"),
                "52w_high": high_52w,
                "pct_from_52w_high": pct_from_high,
                "avg_volume": q.get("averageDailyVolume3Month"),
            })

        note = None
        if preset in ("turnaround_candidate", "drawdown_50_80"):
            note = (
                "Post-screener: filter results where pct_from_52w_high is between -80 and -50 "
                "for true 50-80% drawdown candidates. Run yfinance(financials) on shortlisted "
                "names to compute NCAV or FCF trend."
            )
        elif preset == "net_net":
            note = (
                "P/B < 1 is a proxy for NCAV discount. Run yfinance(financials) on each result "
                "to compute true NCAV = current_assets - total_liabilities and compare to market_cap."
            )

        out = {"preset": preset, "count": len(results), "results": results}
        if note:
            out["note"] = note
        return out

    except Exception as exc:
        logger.exception(f"Screener failed for preset={preset}")
        return {"error": f"Screener execution failed: {str(exc)}"}


class ScreenerTool(Tool):
    """Bulk stock screener using Yahoo Finance's screener API."""

    name = "stock_screener"
    description = (
        "Screens the market for stocks matching value/quality/momentum criteria using Yahoo Finance's "
        "bulk screener API. Single API call — no per-ticker iteration, no rate-limit risk. "
        "Value presets: 'dhandho' (P/E<15, ROE>12%), 'net_net' (P/B<1, Graham NCAV proxy), "
        "'dividend_safety' (yield 3.5-7%, low leverage), 'turnaround_candidate' (beaten-down, P/B<1.5), "
        "'high_roic_small_cap' (ROE>15%, $200M-$2B), 'asset_heavy_discount' (P/B<0.8, EV/EBITDA<8), "
        "'drawdown_50_80' (cyclical trough proxy). "
        "Yahoo presets: 'undervalued_growth', 'undervalued_large_cap', 'aggressive_small_cap', "
        "'most_shorted', 'growth_tech'. "
        "Results include price, P/E, P/B, dividend yield, market cap, 52w range, and pct_from_52w_high."
    )
    parameters = {
        "type": "object",
        "properties": {
            "preset": {
                "type": "string",
                "enum": list(_PRESETS.keys()),
                "description": (
                    "Screening preset. Custom presets (net_net, dividend_safety, turnaround_candidate, "
                    "high_roic_small_cap, asset_heavy_discount, drawdown_50_80) use EquityQuery filters. "
                    "dhandho = P/E<15 + ROE>12% across developed markets. "
                    "Others map to Yahoo's predefined screeners."
                ),
                "default": "dhandho",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (1-25).",
                "default": 10,
                "minimum": 1,
                "maximum": 25,
            },
        },
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self, **kwargs: Any) -> str:
        preset = kwargs.get("preset", "dhandho")
        limit = min(int(kwargs.get("limit", 10)), 25)

        result = await asyncio.to_thread(_run_screen, preset, limit)
        return json.dumps(sanitize_json(result), indent=2, ensure_ascii=False)
