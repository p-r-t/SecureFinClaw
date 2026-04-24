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
# Fibonacci Retracement Levels
# ---------------------------------------------------------------------------

class FibLevels(NamedTuple):
    """Key Fibonacci retracement levels from swing low to swing high."""
    swing_low: float
    swing_high: float
    fib_236: float
    fib_382: float  # primary entry zone
    fib_500: float  # primary entry zone
    fib_618: float  # deep retracement
    current_price: float | None
    nearest_level: str | None   # "38.2%", "50.0%", etc. if within ±1%
    in_entry_zone: bool         # True if price within ±1% of 38.2% or 50.0%


def fibonacci_levels(prices: list[float], lookback: int = 120) -> FibLevels:
    """Compute Fibonacci retracement levels from the most significant swing in the lookback.

    Args:
        prices: List of closing prices (oldest first).
        lookback: Number of bars to scan for swing high and low.
    """
    window = prices[-lookback:] if len(prices) >= lookback else prices
    swing_low = min(window)
    swing_high = max(window)
    rng = swing_high - swing_low

    fib_236 = swing_high - 0.236 * rng
    fib_382 = swing_high - 0.382 * rng
    fib_500 = swing_high - 0.500 * rng
    fib_618 = swing_high - 0.618 * rng

    current = prices[-1] if prices else None
    nearest = None
    in_zone = False

    if current is not None:
        levels = {"23.6%": fib_236, "38.2%": fib_382, "50.0%": fib_500, "61.8%": fib_618}
        closest_dist = float("inf")
        for label, level in levels.items():
            dist = abs(current - level) / level
            if dist < closest_dist:
                closest_dist = dist
                nearest = label
        in_zone = (
            abs(current - fib_382) / fib_382 < 0.01 or
            abs(current - fib_500) / fib_500 < 0.01
        )

    return FibLevels(
        swing_low=swing_low,
        swing_high=swing_high,
        fib_236=round(fib_236, 2),
        fib_382=round(fib_382, 2),
        fib_500=round(fib_500, 2),
        fib_618=round(fib_618, 2),
        current_price=round(current, 2) if current is not None else None,
        nearest_level=nearest,
        in_entry_zone=in_zone,
    )


# ---------------------------------------------------------------------------
# RSI Divergence Detection
# ---------------------------------------------------------------------------

class DivergenceResult(NamedTuple):
    """RSI divergence detection result."""
    bullish_divergence: bool   # price lower low + RSI higher low
    bearish_divergence: bool   # price higher high + RSI lower high
    swing_low_1_idx: int | None
    swing_low_2_idx: int | None
    price_low_1: float | None
    price_low_2: float | None
    rsi_at_low_1: float | None
    rsi_at_low_2: float | None
    description: str


def _find_local_minima(series: list[float], window: int = 5) -> list[int]:
    """Find indices of local minima in a series."""
    minima = []
    for i in range(window, len(series) - window):
        if series[i] == min(series[i - window: i + window + 1]):
            minima.append(i)
    return minima


def _find_local_maxima(series: list[float], window: int = 5) -> list[int]:
    """Find indices of local maxima in a series."""
    maxima = []
    for i in range(window, len(series) - window):
        if series[i] == max(series[i - window: i + window + 1]):
            maxima.append(i)
    return maxima


def detect_rsi_divergence(prices: list[float], lookback: int = 60) -> DivergenceResult:
    """Detect bullish (or bearish) RSI divergence in the most recent lookback bars.

    Bullish divergence: price makes lower low, RSI makes higher low.
    Bearish divergence: price makes higher high, RSI makes lower high.

    Args:
        prices: Full closing price series (oldest first). Needs ≥ 50 bars for RSI to stabilize.
        lookback: Number of recent bars to scan for divergence.
    """
    if len(prices) < 30:
        return DivergenceResult(False, False, None, None, None, None, None, None,
                                "Insufficient data for divergence detection")

    rsi_result = rsi(prices)
    rsi_vals = rsi_result.values

    # Work on the recent window
    prices_window = prices[-lookback:]
    rsi_window = rsi_vals[-lookback:]

    # Filter out None RSI values
    valid_pairs = [(p, r) for p, r in zip(prices_window, rsi_window) if r is not None]
    if len(valid_pairs) < 20:
        return DivergenceResult(False, False, None, None, None, None, None, None,
                                "Insufficient RSI data in lookback window")

    price_w = [p for p, _ in valid_pairs]
    rsi_w = [r for _, r in valid_pairs]

    # Find two most recent swing lows (for bullish divergence)
    minima = _find_local_minima(price_w, window=3)
    bullish = False
    sl1_idx = sl2_idx = p_low1 = p_low2 = r_low1 = r_low2 = None

    if len(minima) >= 2:
        sl1_idx, sl2_idx = minima[-2], minima[-1]
        p_low1, p_low2 = price_w[sl1_idx], price_w[sl2_idx]
        r_low1, r_low2 = rsi_w[sl1_idx], rsi_w[sl2_idx]
        # Bullish: price lower low + RSI higher low
        if p_low2 < p_low1 and r_low2 > r_low1:
            bullish = True

    # Find two most recent swing highs (for bearish divergence)
    maxima = _find_local_maxima(price_w, window=3)
    bearish = False
    if len(maxima) >= 2:
        sh1_idx, sh2_idx = maxima[-2], maxima[-1]
        p_high1, p_high2 = price_w[sh1_idx], price_w[sh2_idx]
        r_high1, r_high2 = rsi_w[sh1_idx], rsi_w[sh2_idx]
        if p_high2 > p_high1 and r_high2 < r_high1:
            bearish = True

    if bullish:
        desc = (f"Bullish divergence: price lower low ({p_low1:.2f} → {p_low2:.2f}) "
                f"with RSI higher low ({r_low1:.1f} → {r_low2:.1f}). "
                "Entry trigger: RSI crossing back above 40.")
    elif bearish:
        desc = "Bearish divergence: price higher high with RSI lower high."
    else:
        desc = "No clear divergence detected in the lookback window."

    return DivergenceResult(
        bullish_divergence=bullish,
        bearish_divergence=bearish,
        swing_low_1_idx=sl1_idx,
        swing_low_2_idx=sl2_idx,
        price_low_1=round(p_low1, 2) if p_low1 is not None else None,
        price_low_2=round(p_low2, 2) if p_low2 is not None else None,
        rsi_at_low_1=round(r_low1, 1) if r_low1 is not None else None,
        rsi_at_low_2=round(r_low2, 1) if r_low2 is not None else None,
        description=desc,
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

    # Fibonacci levels
    fib = fibonacci_levels(prices)
    lines.append("")
    lines.append(f"Swing Low:    ${fib.swing_low:.2f}  |  Swing High: ${fib.swing_high:.2f}")
    lines.append(f"Fib 38.2%:    ${fib.fib_382:.2f}  |  Fib 50.0%: ${fib.fib_500:.2f}  |  Fib 61.8%: ${fib.fib_618:.2f}")
    if fib.in_entry_zone:
        lines.append(f"→ Price is IN Fibonacci entry zone (38.2%–50.0%) — potential support.")
    else:
        lines.append(f"Nearest Fib:  {fib.nearest_level}")

    # RSI Divergence
    div = detect_rsi_divergence(prices)
    lines.append("")
    if div.bullish_divergence:
        lines.append(f"RSI Divergence: BULLISH — {div.description}")
    elif div.bearish_divergence:
        lines.append(f"RSI Divergence: BEARISH — {div.description}")
    else:
        lines.append("RSI Divergence: None detected")

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
