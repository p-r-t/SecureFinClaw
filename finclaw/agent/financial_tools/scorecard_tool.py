"""Fundamental Dhandho Scorecard Tool."""

import json
import math
import pandas as pd
import yfinance as yf
from typing import Any
from pydantic import ConfigDict
from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

class FundamentalScorecardTool(Tool):
    """Calculates a fundamental quality scorecard (ROE, FCF, Debt) over a 5-year period."""

    name = "fundamental_scorecard"
    description = (
        "Evaluates a company's fundamental quality over the last 5 years. "
        "Calculates ROE, FCF stability, and Debt/Equity ratios, and provides Dhandho flags."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g. 'AAPL')."
            },
            "years": {
                "type": "integer",
                "description": "Years of historical data (default 5).",
                "default": 5
            }
        },
        "required": ["ticker"]
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self, **kwargs: Any) -> str:
        ticker_symbol = kwargs.get("ticker", "").upper()
        years = int(kwargs.get("years", 5))
        if not ticker_symbol:
            return json.dumps({"error": "Ticker is required."})

        try:
            t = yf.Ticker(ticker_symbol)
            info = t.info or {}
            
            # Current snapshot
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            market_cap = info.get("marketCap")
            shares_outstanding = info.get("sharesOutstanding")

            pe_ratio = info.get("trailingPE")
            if pe_ratio is None:
                pe_ratio = info.get("forwardPE")
            fcf_ttm = info.get("freeCashflow")
            cash = info.get("totalCash")

            fcf_yield = None
            if fcf_ttm is not None and market_cap and market_cap > 0:
                fcf_yield = fcf_ttm / market_cap

            # yfinance .info provides debtToEquity as a percentage (e.g. 170 = 1.7x)
            debt_equity_raw = info.get("debtToEquity")
            debt_equity = debt_equity_raw / 100 if debt_equity_raw is not None else None

            # Historical data with fuzzy matching
            hist = {"roe": [], "fcf": [], "revenue": [], "net_income": []}
            fcf_cagr = None

            cf = t.cashflow  # Fixed from cash_flow -> cashflow
            inc = t.income_stmt
            bs = t.balance_sheet

            def _is_nan(val):
                try:
                    return val is None or math.isnan(float(val))
                except Exception:
                    return True

            if cf is not None and not cf.empty:
                op_cf_row = None
                capex_row = None
                for label in cf.index:
                    l = str(label).lower()
                    if "operating" in l and "cash" in l:
                        op_cf_row = cf.loc[label]
                    if "capital expenditure" in l or "capex" in l:
                        capex_row = cf.loc[label]

                if op_cf_row is not None:
                    for col in list(cf.columns)[:years]:
                        op = op_cf_row.get(col, None)
                        cap = capex_row.get(col, 0) if capex_row is not None else 0
                        if op is not None and not _is_nan(op):
                            fcf_val = float(op) - abs(float(cap)) if not _is_nan(cap) else float(op)
                            hist["fcf"].append({"year": str(col)[:4], "fcf": round(fcf_val / 1e6, 1)})

                if len(hist["fcf"]) >= 2:
                    oldest = hist["fcf"][-1]["fcf"]
                    newest = hist["fcf"][0]["fcf"]
                    n = len(hist["fcf"]) - 1
                    if oldest > 0 and newest > 0:
                        fcf_cagr = (newest / oldest) ** (1 / n) - 1

            if inc is not None and not inc.empty:
                ni_row = None
                rev_row = None
                for label in inc.index:
                    l = str(label).lower()
                    if "net income" in l and "minority" not in l:
                        ni_row = inc.loc[label]
                    if "total revenue" in l or "revenue" == l:
                        rev_row = inc.loc[label]

                equity_row = None
                if bs is not None and not bs.empty:
                    for label in bs.index:
                        l = str(label).lower()
                        if "stockholder" in l and "equity" in l:
                            equity_row = bs.loc[label]

                for col in list(inc.columns)[:years]:
                    if ni_row is not None and not _is_nan(ni_row.get(col)):
                        ni = float(ni_row.get(col))
                        hist["net_income"].append({"year": str(col)[:4], "net_income_m": round(ni / 1e6, 1)})

                        if equity_row is not None and not _is_nan(equity_row.get(col)):
                            eq = float(equity_row.get(col))
                            if eq > 0:
                                hist["roe"].append({"year": str(col)[:4], "roe": round(ni / eq * 100, 1)})

                    if rev_row is not None and not _is_nan(rev_row.get(col)):
                        hist["revenue"].append({"year": str(col)[:4], "revenue_m": round(float(rev_row.get(col)) / 1e6, 1)})

            roe_avg = None
            if hist["roe"]:
                roe_avg = sum(r["roe"] for r in hist["roe"]) / len(hist["roe"])

            flags = {}
            if pe_ratio is not None:
                flags["pe_lt_15"] = pe_ratio < 15
            if fcf_yield is not None:
                flags["fcf_yield_gt_6pct"] = fcf_yield > 0.06
            if roe_avg is not None:
                flags["roe_avg_gt_15pct"] = roe_avg > 15
            if debt_equity is not None:
                flags["de_lt_0_5"] = debt_equity < 0.5

            payload = {
                "ticker": ticker_symbol,
                "name": info.get("longName"),
                "current": {
                    "price": current_price,
                    "pe_ratio": round(pe_ratio, 2) if pe_ratio else None,
                    "fcf_yield_pct": round(fcf_yield * 100, 2) if fcf_yield else None,
                    "debt_equity": round(debt_equity, 2) if debt_equity is not None else None,
                    "fcf_ttm_m": round(fcf_ttm / 1e6, 1) if fcf_ttm else None,
                    "shares_outstanding_m": round(shares_outstanding / 1e6, 1) if shares_outstanding else None,
                },
                "historical": hist,
                "derived": {
                    "roe_avg_pct": round(roe_avg, 2) if roe_avg else None,
                    "fcf_cagr_pct": round(fcf_cagr * 100, 2) if fcf_cagr else None,
                },
                "dhandho_flags": flags
            }

            return json.dumps(sanitize_json(payload), indent=2)

        except Exception as e:
            return json.dumps({"error": f"Unexpected error: {str(e)}"})
