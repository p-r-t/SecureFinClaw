#!/usr/bin/env python3
"""Technical Indicators — Reference Implementation.

Zero-dependency (only stdlib + basic math) calculator for RSI, MACD, SMA, and EMA.
Designed to be executed by the FinClaw agent via the Python environment tool
when precise indicator values are needed.

Usage:
    python indicators.py              # runs the built-in demo with sample data
    # Or import and call functions directly with your own price series.

All functions accept a plain list of floats (closing prices, oldest first).
"""

from __future__ import annotations

import math
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Simple & Exponential Moving Averages
# ---------------------------------------------------------------------------

def sma(prices: list[float], period: int) -> list[float | None]:
    """Simple Moving Average.

    Returns a list the same length as prices. The first (period - 1) entries
    are None because there is not enough data to compute the average.
    """
    result: list[float | None] = [None] * (period - 1)
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1 : i + 1]
        result.append(sum(window) / period)
    return result


def ema(prices: list[float], period: int) -> list[float | None]:
    """Exponential Moving Average (using multiplier = 2 / (period + 1)).

    The first (period - 1) entries are None. The EMA seed (index period-1)
    is the SMA of the first `period` prices.
    """
    if len(prices) < period:
        return [None] * len(prices)

    multiplier = 2.0 / (period + 1)
    result: list[float | None] = [None] * (period - 1)

    # Seed with SMA
    seed = sum(prices[:period]) / period
    result.append(seed)

    for i in range(period, len(prices)):
        prev = result[-1]
        assert prev is not None  # guaranteed by construction
        value = (prices[i] - prev) * multiplier + prev
        result.append(value)

    return result


# ---------------------------------------------------------------------------
# RSI (Wilder's Smoothing, 14-period default)
# ---------------------------------------------------------------------------

class RSIResult(NamedTuple):
    """RSI calculation result."""
    values: list[float | None]  # RSI at each bar (None where insufficient data)
    current: float | None       # most recent RSI value


def rsi(prices: list[float], period: int = 14) -> RSIResult:
    """Relative Strength Index using Wilder's smoothed moving average.

    Returns RSIResult with the full series and the current (latest) value.
    """
    if len(prices) < period + 1:
        return RSIResult(values=[None] * len(prices), current=None)

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [abs(min(d, 0.0)) for d in deltas]

    # Seed averages (simple average of first `period` values)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values: list[float | None] = [None] * period  # first bar has no delta

    def _calc_rsi(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        rs = ag / al
        return 100.0 - (100.0 / (1.0 + rs))

    rsi_values.append(_calc_rsi(avg_gain, avg_loss))

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rsi_values.append(_calc_rsi(avg_gain, avg_loss))

    return RSIResult(values=rsi_values, current=rsi_values[-1])


# ---------------------------------------------------------------------------
# MACD (12, 26, 9 default)
# ---------------------------------------------------------------------------

class MACDResult(NamedTuple):
    """MACD calculation result."""
    macd_line: list[float | None]
    signal_line: list[float | None]
    histogram: list[float | None]
    current_macd: float | None
    current_signal: float | None
    current_histogram: float | None
    crossover: str  # "bullish", "bearish", or "none"


def macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> MACDResult:
    """MACD indicator.

    Returns MACDResult with the full series and current values,
    plus a crossover classification based on the last two bars.
    """
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)

    # MACD line = EMA_fast - EMA_slow
    macd_line: list[float | None] = []
    for ef, es in zip(ema_fast, ema_slow):
        if ef is not None and es is not None:
            macd_line.append(ef - es)
        else:
            macd_line.append(None)

    # Signal line = EMA of MACD line (only over non-None values)
    macd_values = [v for v in macd_line if v is not None]
    if len(macd_values) >= signal_period:
        signal_raw = ema(macd_values, signal_period)
        # Re-align: pad with None for the leading None entries in macd_line
        leading_nones = len(macd_line) - len(macd_values)
        signal_line: list[float | None] = [None] * leading_nones + signal_raw
    else:
        signal_line = [None] * len(macd_line)

    # Histogram
    histogram: list[float | None] = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(m - s)
        else:
            histogram.append(None)

    # Current values
    current_macd = macd_line[-1] if macd_line and macd_line[-1] is not None else None
    current_signal = signal_line[-1] if signal_line and signal_line[-1] is not None else None
    current_hist = histogram[-1] if histogram and histogram[-1] is not None else None

    # Crossover detection (compare last two bars)
    crossover = "none"
    if len(histogram) >= 2:
        h_prev = histogram[-2]
        h_curr = histogram[-1]
        if h_prev is not None and h_curr is not None:
            if h_prev <= 0 and h_curr > 0:
                crossover = "bullish"
            elif h_prev >= 0 and h_curr < 0:
                crossover = "bearish"

    return MACDResult(
        macd_line=macd_line,
        signal_line=signal_line,
        histogram=histogram,
        current_macd=current_macd,
        current_signal=current_signal,
        current_histogram=current_hist,
        crossover=crossover,
    )


# ---------------------------------------------------------------------------
# Convenience: full analysis from a price list
# ---------------------------------------------------------------------------

def analyze(prices: list[float], ticker: str = "UNKNOWN") -> str:
    """Run full technical analysis and return a formatted report string.

    Args:
        prices: List of closing prices (oldest first, at least 50 bars).
        ticker: Ticker symbol for display purposes.
    """
    if len(prices) < 30:
        return f"ERROR: Need at least 30 closing prices, got {len(prices)}."

    r = rsi(prices)
    m = macd(prices)
    sma_50 = sma(prices, min(50, len(prices)))
    sma_200 = sma(prices, 200) if len(prices) >= 200 else None

    current_price = prices[-1]
    current_rsi = r.current
    sma50_val = sma_50[-1] if sma_50 and sma_50[-1] is not None else None
    sma200_val = sma_200[-1] if sma_200 and sma_200[-1] is not None else None

    # RSI classification
    if current_rsi is not None:
        if current_rsi < 25:
            rsi_label = "Deeply Oversold"
        elif current_rsi < 30:
            rsi_label = "Oversold"
        elif current_rsi < 50:
            rsi_label = "Below Neutral"
        elif current_rsi < 70:
            rsi_label = "Neutral/Bullish"
        else:
            rsi_label = "Overbought"
    else:
        rsi_label = "N/A"

    # MACD classification
    if m.current_histogram is not None:
        if m.crossover == "bullish":
            macd_label = "Bullish Crossover"
        elif m.crossover == "bearish":
            macd_label = "Bearish Crossover"
        elif m.current_histogram > 0:
            macd_label = "Bullish"
        else:
            macd_label = "Bearish"
    else:
        macd_label = "N/A"

    lines = [
        f"=== Technical Analysis: {ticker} ===",
        f"Price: ${current_price:.2f}",
        "",
        f"RSI (14):     {current_rsi:.2f}  — {rsi_label}" if current_rsi else "RSI (14):     N/A",
        f"MACD:         {m.current_macd:.4f}" if m.current_macd is not None else "MACD:         N/A",
        f"Signal:       {m.current_signal:.4f}" if m.current_signal is not None else "Signal:       N/A",
        f"Histogram:    {m.current_histogram:.4f}  — {macd_label}" if m.current_histogram is not None else f"Histogram:    N/A  — {macd_label}",
        f"Crossover:    {m.crossover}",
        "",
    ]

    if sma50_val is not None:
        pct_from_50 = ((current_price - sma50_val) / sma50_val) * 100
        pos = "Above" if current_price >= sma50_val else "Below"
        lines.append(f"SMA-50:       ${sma50_val:.2f}  — Price is {pos} ({pct_from_50:+.1f}%)")

    if sma200_val is not None:
        pct_from_200 = ((current_price - sma200_val) / sma200_val) * 100
        pos = "Above" if current_price >= sma200_val else "Below"
        lines.append(f"SMA-200:      ${sma200_val:.2f}  — Price is {pos} ({pct_from_200:+.1f}%)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simulated 60-day closing prices for a stock recovering from a dip
    import random
    random.seed(42)

    base = 100.0
    demo_prices = []
    for i in range(120):
        # Trend: dip then recover
        if i < 40:
            drift = -0.15
        elif i < 80:
            drift = 0.25
        else:
            drift = 0.05
        base += drift + random.gauss(0, 1.2)
        base = max(base, 10.0)  # floor
        demo_prices.append(round(base, 2))

    print(analyze(demo_prices, ticker="DEMO"))
    print()

    # Show last 5 RSI values
    r = rsi(demo_prices)
    print(f"Last 5 RSI values: {[round(v, 2) if v else None for v in r.values[-5:]]}")

    m = macd(demo_prices)
    print(f"Last 5 Histogram values: {[round(v, 4) if v else None for v in m.histogram[-5:]]}")
    print(f"Crossover: {m.crossover}")
