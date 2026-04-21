---
name: market-regime
description: >
  Determines the current market regime (Bull, Caution, Bear) using breadth and moving averages on major market indices and sector ETFs. Use this skill BEFORE making value investing decisions to determine the appropriate Margin of Safety. Also triggers for "what is the market regime", "are we in a bull market", "check market breadth", or "is it safe to invest".
---

# Market Regime Analysis

**Your role:** You are a macro overlay specialist. Your job is to classify the current market environment to protect the portfolio from systemic risk. A "cheap" stock in a bear market is often a value trap.

**Output:** A "Regime Card" that dictates the required Margin of Safety for all downstream value investing activities.

---

## Step 1 — Gather Market Data

You will use only the native `yfinance` tool to gather daily closing prices for the last 200 trading days. You do not need external API keys.

1. **Broad Market Trend:**
   Fetch historical data for the S&P 500 ETF (SPY) and Volatility Index (^VIX).
   ```
   yfinance(command="history", symbol="SPY", period="1y")
   yfinance(command="history", symbol="^VIX", period="1mo")
   ```

2. **Sector Breadth (The "Engine"):**
   Fetch data for key sector ETFs to see if participation is broad or narrow.
   - Technology: XLK
   - Financials: XLF
   - Energy: XLE
   - Healthcare: XLV
   - Industrials: XLI
   - Utilities: XLU

---

## Step 2 — Calculate Indicators

From the gathered data, calculate the following:

1. **SPY Trend:** Is SPY current price > SPY 200-day Simple Moving Average (SMA)?
2. **Breadth %:** Of the 6 sector ETFs, what percentage are trading *above* their respective 200-day SMAs?
3. **VIX Level:** Is the VIX < 20 (Complacence/Normal), 20-30 (Elevated/Transition), or > 30 (Fear/Crisis)?

---

## Step 3 — Classify Regime

Compare your indicators against this matrix to classify the current regime:

| Regime | SPY vs 200d | Breadth (>200d) | VIX | Required MoS |
|--------|-------------|-----------------|-----|--------------|
| **Bull (Healthy)** | Above | ≥ 66% (4+ sectors) | < 20 | **30%** (Normal) |
| **Bull (Narrowing)** | Above | < 33% (1-2 sectors) | < 25 | **50%** (Elevated) |
| **Caution (Late Cycle)**| Below | ≥ 50% (3+ sectors) | 20-30 | **50%** (Elevated) |
| **Bear (Correction)** | Below | < 33% (1-2 sectors) | > 25 | **65%** (High) |
| **Bear (Crisis)** | Below | 0% (0 sectors) | > 35 | **75%** (Maximum) |

*Note: If the indicators send mixed signals, default to the more conservative regime.*

---

## Output — Regime Card

Output the following exact format so that downstream skills (like `value-investing`) can parse it.

```
# 🌍 Market Regime Card
*Date: [CURRENT DATE]*

### Indicators
- **SPY Trend:** [Above/Below] 200-day SMA ($[Current] vs $[SMA])
- **Sector Breadth:** [X]/6 Sectors Above 200d SMA ([List of sectors holding up])
- **Volatility (VIX):** [Current VIX]

### Classification
**Regime:** [Regime Name from Matrix]

### Valuation Directive
⚠️ **Required Margin of Safety:** [XX]%

*Instruction for downstream skills: Any DCF valuation performed in this session MUST use [XX]% as the minimum Margin of Safety threshold.*
```

## Cross-References
- **value-investing**: downstream analysis that will consume the Regime Card's MoS directive.
