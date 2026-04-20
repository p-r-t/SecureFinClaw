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

# Preset → Yahoo predefined screen name mapping
_PRESETS: dict[str, str | None] = {
    "dhandho": None,               # Custom multi-region EquityQuery (built below)
    "undervalued_growth": "undervalued_growth_stocks",
    "undervalued_large_cap": "undervalued_large_caps",
    "aggressive_small_cap": "aggressive_small_caps",
    "most_shorted": "most_shorted_stocks",
    "growth_tech": "growth_technology_stocks",
}


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


def _run_screen(preset: str, limit: int) -> dict:
    """Synchronous wrapper — executed in a thread."""
    try:
        # Resolve query
        if preset == "dhandho":
            query = _build_dhandho_query()
            if query is None:
                # Fallback if EquityQuery is unavailable
                query = "undervalued_growth_stocks"
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
            results.append({
                "symbol": q.get("symbol"),
                "name": q.get("shortName") or q.get("longName"),
                "price": q.get("regularMarketPrice"),
                "change_pct": q.get("regularMarketChangePercent"),
                "pe_ratio": q.get("trailingPE"),
                "forward_pe": q.get("forwardPE"),
                "market_cap": q.get("marketCap"),
                "52w_low": q.get("fiftyTwoWeekLow"),
                "52w_high": q.get("fiftyTwoWeekHigh"),
                "avg_volume": q.get("averageDailyVolume3Month"),
            })

        return {
            "preset": preset,
            "count": len(results),
            "results": results,
        }

    except Exception as exc:
        logger.exception(f"Screener failed for preset={preset}")
        return {"error": f"Screener execution failed: {str(exc)}"}


class ScreenerTool(Tool):
    """Bulk stock screener using Yahoo Finance's screener API."""

    name = "stock_screener"
    description = (
        "Screens the market for stocks matching value/quality criteria using Yahoo Finance's "
        "bulk screener API. Single API call — no per-ticker iteration, no rate-limit risk. "
        "Available presets: 'dhandho' (P/E<15 US large-caps), 'undervalued_growth', "
        "'undervalued_large_cap', 'aggressive_small_cap', 'most_shorted', 'growth_tech'. "
        "Returns up to 25 matching tickers with price, P/E, market cap, and 52-week range."
    )
    parameters = {
        "type": "object",
        "properties": {
            "preset": {
                "type": "string",
                "enum": list(_PRESETS.keys()),
                "description": (
                    "Screening preset. 'dhandho' = custom P/E<15 + US + >$1B market cap. "
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
