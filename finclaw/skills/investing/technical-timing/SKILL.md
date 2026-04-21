---
name: technical-timing
description: >
  Analyze technical indicators (RSI, MACD, moving averages) to determine optimal entry timing for a fundamentally sound stock. Use this skill AFTER completing value analysis and before sizing the bet. Also triggers for "check RSI", "MACD signal", "is it a good time to buy", "technical analysis", or "entry timing".
---

# Technical Timing — Entry Signal Analysis

**Your role:** You are a disciplined execution specialist. Fundamental analysis has already identified the stock as potentially undervalued. Your job is to determine whether *right now* is the right time to commit capital, or whether patience will yield a better entry.

**Philosophy:** We are not day traders. We use technical indicators as a *confirmation filter* on value theses, not as standalone trading signals. A stock that is fundamentally cheap but technically in freefall (falling knife) is best entered gradually or after stabilization.

---

## Step 1 — Gather Price Data

Fetch 6 months of daily OHLCV data for the target ticker:

```
yfinance(command="historical", symbol="<TICKER>", start_date="<6 months ago>", end_date="<today>", interval="1d")
```

You need at least 50 data points for reliable indicator calculation. If fewer than 50 bars are returned, extend the lookback to 1 year.

---

## Step 2 — Calculate Indicators

From the closing prices, compute:

### 2a — RSI (14-period)
1. Calculate daily price changes: `delta = close[i] - close[i-1]`
2. Separate gains (positive deltas) and losses (absolute value of negative deltas)
3. Calculate the initial average gain and average loss over the first 14 periods (simple average)
4. Smooth subsequent values: `avg_gain = (prev_avg_gain * 13 + current_gain) / 14`
5. RS = avg_gain / avg_loss
6. RSI = 100 - (100 / (1 + RS))

### 2b — MACD (12, 26, 9)
1. EMA-12: 12-period Exponential Moving Average of closing prices
2. EMA-26: 26-period Exponential Moving Average of closing prices
3. MACD Line = EMA-12 − EMA-26
4. Signal Line = 9-period EMA of MACD Line
5. Histogram = MACD Line − Signal Line

### 2c — Trend Context
1. SMA-50: 50-period Simple Moving Average
2. SMA-200: 200-period Simple Moving Average (if enough data)
3. Price vs SMA-50: Above or Below?

**CRITICAL RULE:** If you have access to the Python environment, you may execute `scripts/indicators.py` (in this skill's directory) to compute these values accurately. Do NOT estimate these in your head.

---

## Step 3 — Classify Entry Signal

Compare your calculated indicators against this decision matrix:

| Signal | RSI | MACD | Price vs SMA-50 | Recommendation |
|--------|-----|------|-----------------|----------------|
| **Strong Buy** | 30–50 (recovering from oversold) | Bullish crossover (MACD > Signal, histogram turning positive) | Near or above | **Enter Now** — momentum is confirming the value thesis |
| **Buy** | 40–60 (neutral zone) | Bullish (MACD > Signal) | Above | **Enter Now** — no red flags |
| **Cautious Buy** | 50–70 | Mixed (histogram shrinking or flat) | Above | **Scale In** — enter 50% now, 50% over 2–4 weeks |
| **Wait (Overbought)** | > 70 | Bearish divergence or crossover imminent | Well above | **Wait** — technically extended; let it pull back to SMA-50 |
| **Wait (Falling Knife)** | < 30 | Bearish (MACD < Signal, histogram widening negative) | Below | **Wait** — oversold but still falling; wait for RSI to cross back above 30 |
| **Scale In (Capitulation)** | < 25 | Deeply negative but histogram starting to narrow | Well below | **Scale In** — early signs of bottoming; enter 25% now, add on confirmation |

**Tiebreaker rule:** If RSI and MACD give conflicting signals, defer to the more conservative recommendation.

---

## Output — Timing Card

```
# ⏱️ Technical Timing: [TICKER]
*Date: [CURRENT DATE]*

### Indicators
- **RSI (14):** [Value] — [Oversold / Neutral / Overbought]
- **MACD:** Line [Value] | Signal [Value] | Histogram [Value] — [Bullish / Bearish / Neutral]
- **Price vs SMA-50:** $[Price] vs $[SMA-50] — [Above / Below] ([X]% away)
- **Price vs SMA-200:** $[Price] vs $[SMA-200] — [Above / Below] (if available)

### Signal Classification
**Entry Signal:** [Signal Name from Matrix]

### ⏱️ Entry Recommendation
**[Enter Now / Scale In / Wait]**

[1–2 sentences explaining rationale, e.g., "RSI at 42 with a fresh MACD bullish crossover suggests momentum is shifting in favor of the value thesis. Enter full position."]

*If Wait: Specify the trigger to re-evaluate (e.g., "Re-check when RSI crosses above 30" or "Wait for MACD bullish crossover").*
```

---

## Common Pitfalls
- **RSI divergence:** If price makes a new low but RSI makes a higher low, this is a *bullish divergence* and one of the strongest buy signals. Flag it explicitly.
- **MACD in range-bound markets:** MACD generates frequent false crossovers when a stock is trading sideways. If 50-day average true range is < 2%, note that MACD signals are less reliable.
- **Overbought ≠ Sell:** An RSI above 70 does not mean the stock is overvalued. It means momentum is extended. In strong uptrends, RSI can stay above 70 for weeks.
- **Volume confirmation:** If the MACD bullish crossover occurs on above-average volume, the signal is stronger. Mention volume context if available.

## Cross-References
- **value-investing**: upstream — provides the fundamental "Pass" that justifies looking at entry timing
- **investment-critic**: upstream — ensures risks have been red-teamed before timing the entry
- **bet-sizing**: downstream — once timing is confirmed, pass to bet-sizing to determine position size
- **market-regime**: macro context — if regime is "Bear (Crisis)", technical-timing should default to "Scale In" at most, never "Enter Now"
- **historical-risk**: realized volatility informs whether current ATR is elevated relative to history
