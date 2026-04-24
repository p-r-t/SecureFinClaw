"""Relative Strength Tool — price-ratio momentum vs. benchmark and sector ETF ranking.

Uses yfinance for all data (free). No paid sources required.

Commands:
  vs_benchmark    - Compare a stock's price return against SPY over 1M/3M/6M/12M
  sector_ranking  - Rank the 11 GICS sectors by relative strength vs SPY
  top_in_sector   - Find the highest-RS stock(s) within a given sector ETF or list
"""

from __future__ import annotations

import asyncio
import json
from datetime import date, timedelta
from typing import Any

import yfinance as yf
from loguru import logger

from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json


# ---------------------------------------------------------------------------
# Sector ETF universe (SPDR sector ETFs — free data on yfinance)
# ---------------------------------------------------------------------------

SECTOR_ETFS: dict[str, str] = {
    "XLK":  "Technology",
    "XLV":  "Healthcare",
    "XLF":  "Financials",
    "XLY":  "Consumer Discretionary",
    "XLP":  "Consumer Staples",
    "XLE":  "Energy",
    "XLI":  "Industrials",
    "XLB":  "Materials",
    "XLRE": "Real Estate",
    "XLU":  "Utilities",
    "XLC":  "Communication Services",
}

BENCHMARK = "SPY"

_PERIODS: dict[str, int] = {
    "1m": 30,
    "3m": 91,
    "6m": 182,
    "12m": 365,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct_change(series, days: int) -> float | None:
    """Compute percentage change over the last N calendar days from a price Series."""
    if series is None or series.empty:
        return None
    end_price = float(series.iloc[-1])
    start_date = series.index[-1].to_pydatetime().date() - timedelta(days=days)
    candidates = series[series.index.date <= start_date]  # type: ignore[attr-defined]
    if candidates.empty:
        return None
    start_price = float(candidates.iloc[-1])
    if start_price == 0:
        return None
    return round(((end_price - start_price) / start_price) * 100, 2)


def _fetch_prices(symbol: str, days: int = 400) -> Any:
    """Fetch closing price history for a symbol."""
    try:
        start = (date.today() - timedelta(days=days)).isoformat()
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start, interval="1d")
        if hist.empty:
            return None
        return hist["Close"]
    except Exception as exc:
        logger.debug(f"relative_strength: price fetch failed for {symbol}: {exc}")
        return None


def _rs_score(symbol: str, benchmark_series) -> dict:
    """Compute RS score = average of 1M, 3M, 6M relative returns vs benchmark."""
    prices = _fetch_prices(symbol)
    if prices is None:
        return {"symbol": symbol, "error": "price data unavailable"}

    rows: dict[str, Any] = {"symbol": symbol}
    rs_values = []
    for period_label, days in _PERIODS.items():
        stock_ret = _pct_change(prices, days)
        bench_ret = _pct_change(benchmark_series, days)
        if stock_ret is not None and bench_ret is not None:
            rel = round(stock_ret - bench_ret, 2)
            rows[f"return_{period_label}"] = stock_ret
            rows[f"rs_{period_label}"] = rel
            rs_values.append(rel)
        else:
            rows[f"return_{period_label}"] = None
            rows[f"rs_{period_label}"] = None

    rows["rs_composite"] = round(sum(rs_values) / len(rs_values), 2) if rs_values else None
    rows["current_price"] = round(float(prices.iloc[-1]), 2) if not prices.empty else None
    return rows


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def _cmd_vs_benchmark(symbol: str) -> dict:
    """Compare a single stock vs SPY across 1M/3M/6M/12M."""
    bench = _fetch_prices(BENCHMARK)
    if bench is None:
        return {"error": "Failed to fetch SPY benchmark data"}

    result = _rs_score(symbol, bench)
    result["benchmark"] = BENCHMARK

    # Classification
    composite = result.get("rs_composite")
    if composite is not None:
        if composite >= 10:
            result["classification"] = "Strong Leader"
        elif composite >= 3:
            result["classification"] = "Market Leader"
        elif composite >= -3:
            result["classification"] = "Inline"
        elif composite >= -10:
            result["classification"] = "Laggard"
        else:
            result["classification"] = "Severe Laggard"

    return result


def _cmd_sector_ranking() -> dict:
    """Rank all 11 GICS sector ETFs by composite RS vs SPY."""
    bench = _fetch_prices(BENCHMARK)
    if bench is None:
        return {"error": "Failed to fetch SPY benchmark data"}

    rankings = []
    for etf, sector_name in SECTOR_ETFS.items():
        row = _rs_score(etf, bench)
        row["sector"] = sector_name
        rankings.append(row)

    rankings.sort(key=lambda x: x.get("rs_composite") or -999, reverse=True)
    for i, row in enumerate(rankings, 1):
        row["rank"] = i

    return {
        "benchmark": BENCHMARK,
        "as_of": date.today().isoformat(),
        "sectors": rankings,
        "top_2": [r["symbol"] for r in rankings[:2]],
        "bottom_2": [r["symbol"] for r in rankings[-2:]],
        "note": (
            "Top sectors show strongest price momentum relative to SPY. "
            "For Sector Rotation and Cyclical funnels: pick the top-2 sectors, "
            "then run top_in_sector to find the highest-RS individual stock within each."
        ),
    }


def _cmd_top_in_sector(symbols: list[str], top_n: int = 3) -> dict:
    """Rank a list of stocks by RS vs SPY and return the top N."""
    bench = _fetch_prices(BENCHMARK)
    if bench is None:
        return {"error": "Failed to fetch SPY benchmark data"}

    results = []
    for sym in symbols:
        row = _rs_score(sym, bench)
        results.append(row)

    results = [r for r in results if "error" not in r]
    results.sort(key=lambda x: x.get("rs_composite") or -999, reverse=True)

    return {
        "benchmark": BENCHMARK,
        "as_of": date.today().isoformat(),
        "ranked": results,
        "top_picks": [r["symbol"] for r in results[:top_n]],
    }


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class RelativeStrengthTool(Tool):
    """Relative strength analysis vs. SPY benchmark and sector ETF ranking."""

    name = "relative_strength"
    description = (
        "Compute price-ratio relative strength (RS) vs the SPY benchmark across 1M/3M/6M/12M windows. "
        "Commands: "
        "'vs_benchmark' = score a single stock vs SPY (RS composite + classification); "
        "'sector_ranking' = rank all 11 GICS sector ETFs by composite RS — outputs top-2 and bottom-2 "
        "sectors, useful for Sector Rotation and Cyclical/Peak-Pessimism funnels; "
        "'top_in_sector' = rank a list of ticker symbols by RS to find the highest-momentum name "
        "within a sector. All data from yfinance — no paid source required."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["vs_benchmark", "sector_ranking", "top_in_sector"],
                "description": "Operation to perform.",
            },
            "symbol": {
                "type": "string",
                "description": "Stock ticker. Required for vs_benchmark.",
            },
            "symbols": {
                "type": "string",
                "description": (
                    "Comma-separated tickers to rank. Required for top_in_sector. "
                    "E.g. 'AAPL,MSFT,NVDA,AMZN'."
                ),
            },
            "top_n": {
                "type": "integer",
                "description": "Number of top results to highlight in top_in_sector. Default: 3.",
                "minimum": 1,
                "maximum": 20,
            },
        },
        "required": ["command"],
    }

    async def execute(self, **kwargs: Any) -> str:
        command = kwargs.get("command", "")
        logger.info(f"relative_strength command={command}")

        if command == "vs_benchmark":
            symbol = (kwargs.get("symbol") or "").strip().upper()
            if not symbol:
                return json.dumps({"error": "symbol is required for vs_benchmark"})
            result = await asyncio.to_thread(_cmd_vs_benchmark, symbol)

        elif command == "sector_ranking":
            result = await asyncio.to_thread(_cmd_sector_ranking)

        elif command == "top_in_sector":
            symbols_str = (kwargs.get("symbols") or "").strip()
            if not symbols_str:
                return json.dumps({"error": "symbols is required for top_in_sector"})
            symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
            top_n = int(kwargs.get("top_n", 3))
            result = await asyncio.to_thread(_cmd_top_in_sector, symbols, top_n)

        else:
            result = {"error": f"Unknown command: {command!r}"}

        return json.dumps(sanitize_json(result), indent=2, ensure_ascii=False)
