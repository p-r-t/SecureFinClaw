---
name: momentum
description: >
  Perform a momentum and technical analysis on a specific ticker (stock or ETF).
  Use this skill when the user provides a ticker and asks to: run a momentum analysis,
  check RSI, MACD, or moving averages, find chart patterns, or ask "is X trending well?".
  Also triggers for casual phrasings like "what is the momentum on TICKER",
  or "is this overbought?".
---

# Momentum Trading Analysis

Evaluates the price action and momentum strength of a given asset (stock or ETF). Requires a ticker as input.
Produces a **structured markdown report** across three stages: Trend Identification → Momentum & Reversals → Volatility & Patterns.

---

## Stage 1 — Trend Identification

**Goal:** Establish the primary and secondary trends using Simple Moving Averages (SMA).

Call `momentum_analyzer` with `ticker`:
```python
momentum_analyzer(ticker="TICK")
```

**Pass/Fail criteria:**

| Metric | Target | Flag |
|--------|--------|------|
| Price vs 200-SMA | Price > 200 SMA (Long-term Bullish) | `price_above_200_sma` |
| Price vs 50-SMA | Price > 50 SMA (Short-term Bullish) | `price_above_50_sma` |
| 50-SMA vs 200-SMA | 50 SMA > 200 SMA (Golden Cross) | `sma_50_above_200` |

**Output:**
```markdown
### 📈 Stage 1: Trend Identification — [TICKER]

| Metric       | Value  | Target  | Pass/Fail |
|--------------|--------|---------|-----------|
| Price / 200-SMA | ... | > 200-SMA | ✅ / ❌   |
| Price / 50-SMA  | ... | > 50-SMA  | ✅ / ❌   |
| 50/200 SMA Cross| ... | Golden Cross | ✅ / ❌ |

**Verdict:** [Bullish / Bearish / Neutral Trend]
```

---

## Stage 2 — Momentum Strength & Reversals

**Goal:** Assess whether the trend has strong backing or is overextended.

**Metrics:**
- **RSI (14)**: > 70 is overbought, < 30 is oversold. Between 40 and 60 is neutral.
- **MACD (12,26,9)**: If MACD > Signal Line, momentum is positive. If MACD < Signal Line, momentum is negative.

**Output:**
```markdown
### ⚡ Stage 2: Momentum Strength — [TICKER]

- **RSI (14):** [Value] - [Overbought / Oversold / Neutral]
- **MACD vs Signal:** [MACD] vs [Signal] - [Positive / Negative Momentum]

**Verdict:** [Strong Momentum / Weakening / Reversal Risk]
```

---

## Stage 3 — Volatility & Chart Patterns

**Goal:** Identify volatility boundaries and structural pricing patterns.

**Metrics:**
- **Bollinger Bands (20,2)**: If price is near the upper band, it may revert. If near the lower band, it may bounce.
- **52-Week High/Low Proximity**: Is the asset breaking out to new highs or bouncing off lows?

**Output:**
```markdown
### 📊 Stage 3: Volatility & Patterns — [TICKER]

- **Bollinger Bands:** Price is [Near Upper / Near Lower / Mid-band].
- **52-Week Range:** [Value] away from 52-week High.

**Verdict:** [e.g., Breakout Setup / Mean Reversion Setup / Chopping]
```

---

## Overall Verdict & Action

Combine the three stages to provide a final action plan.

```markdown
**Verdict:** [Brief summary of the setup]
**Action:** 
- [ ] Buy/Long (Strong trend, good momentum, not overextended)
- [ ] Watchlist (Wait for pullback to SMA or MACD crossover)
- [ ] Sell/Avoid (Bearish trend or extremely overbought)
```
