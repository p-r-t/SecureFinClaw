"""Momentum and Technical Analysis Tool."""

import json
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Any
from pydantic import ConfigDict
from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

class MomentumTool(Tool):
    """Calculates momentum indicators (SMA, RSI, MACD, Bollinger Bands) for a given ticker."""

    name = "momentum_analyzer"
    description = (
        "Evaluates the momentum and technical trend of a ticker. "
        "Calculates 50-day and 200-day SMAs, RSI (14), MACD, and Bollinger Bands."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock or ETF ticker symbol (e.g. 'AAPL', 'SPY')."
            }
        },
        "required": ["ticker"]
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self, **kwargs: Any) -> str:
        ticker_symbol = kwargs.get("ticker", "").upper()
        if not ticker_symbol:
            return json.dumps({"error": "Ticker is required."})

        try:
            # Use yfinance with standard caching/optimization
            t = yf.Ticker(ticker_symbol)
            
            # Fetch 2 years of data to ensure enough periods for 200 SMA
            hist = t.history(period="2y", interval="1d")
            
            if hist.empty:
                return json.dumps({"error": f"No historical data found for {ticker_symbol}."})

            close_prices = hist['Close']
            
            # Basic Price
            current_price = float(close_prices.iloc[-1])
            
            # 52-Week High / Low
            last_1y = hist.last('365D')
            if not last_1y.empty:
                high_52w = float(last_1y['High'].max())
                low_52w = float(last_1y['Low'].min())
                pct_from_high = ((current_price - high_52w) / high_52w) * 100
            else:
                high_52w = None
                low_52w = None
                pct_from_high = None

            # SMAs
            sma_50 = float(close_prices.rolling(window=50).mean().iloc[-1]) if len(close_prices) >= 50 else None
            sma_200 = float(close_prices.rolling(window=200).mean().iloc[-1]) if len(close_prices) >= 200 else None

            # RSI (14)
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1]) if len(rsi.dropna()) > 0 else None

            # MACD (12, 26, 9)
            ema_12 = close_prices.ewm(span=12, adjust=False).mean()
            ema_26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_hist = macd_line - signal_line
            
            current_macd = float(macd_line.iloc[-1]) if len(macd_line.dropna()) > 0 else None
            current_signal = float(signal_line.iloc[-1]) if len(signal_line.dropna()) > 0 else None
            current_macd_hist = float(macd_hist.iloc[-1]) if len(macd_hist.dropna()) > 0 else None

            # Bollinger Bands (20, 2)
            sma_20 = close_prices.rolling(window=20).mean()
            std_20 = close_prices.rolling(window=20).std()
            upper_band = sma_20 + (std_20 * 2)
            lower_band = sma_20 - (std_20 * 2)
            
            current_upper = float(upper_band.iloc[-1]) if len(upper_band.dropna()) > 0 else None
            current_lower = float(lower_band.iloc[-1]) if len(lower_band.dropna()) > 0 else None
            current_mid = float(sma_20.iloc[-1]) if len(sma_20.dropna()) > 0 else None

            payload = {
                "ticker": ticker_symbol,
                "current_price": round(current_price, 2),
                "trend": {
                    "sma_50": round(sma_50, 2) if sma_50 is not None else None,
                    "sma_200": round(sma_200, 2) if sma_200 is not None else None,
                    "price_vs_50sma": "Above" if (sma_50 and current_price > sma_50) else "Below" if sma_50 else None,
                    "price_vs_200sma": "Above" if (sma_200 and current_price > sma_200) else "Below" if sma_200 else None,
                    "golden_cross": True if (sma_50 and sma_200 and sma_50 > sma_200) else False if (sma_50 and sma_200) else None
                },
                "momentum": {
                    "rsi_14": round(current_rsi, 2) if current_rsi is not None else None,
                    "rsi_status": "Overbought" if (current_rsi and current_rsi > 70) else "Oversold" if (current_rsi and current_rsi < 30) else "Neutral",
                    "macd": {
                        "macd_line": round(current_macd, 3) if current_macd is not None else None,
                        "signal_line": round(current_signal, 3) if current_signal is not None else None,
                        "histogram": round(current_macd_hist, 3) if current_macd_hist is not None else None,
                        "status": "Bullish (MACD > Signal)" if (current_macd is not None and current_signal is not None and current_macd > current_signal) else "Bearish (MACD < Signal)"
                    }
                },
                "volatility_and_patterns": {
                    "bollinger_bands": {
                        "upper": round(current_upper, 2) if current_upper is not None else None,
                        "mid": round(current_mid, 2) if current_mid is not None else None,
                        "lower": round(current_lower, 2) if current_lower is not None else None,
                        "price_position": "Near Upper Band" if (current_upper and current_price >= current_upper * 0.98) else "Near Lower Band" if (current_lower and current_price <= current_lower * 1.02) else "Mid-band"
                    },
                    "52_week_range": {
                        "high": round(high_52w, 2) if high_52w is not None else None,
                        "low": round(low_52w, 2) if low_52w is not None else None,
                        "pct_from_high": round(pct_from_high, 2) if pct_from_high is not None else None
                    }
                }
            }

            return json.dumps(sanitize_json(payload), indent=2)

        except Exception as e:
            return json.dumps({"error": f"Unexpected error calculating momentum: {str(e)}"})
