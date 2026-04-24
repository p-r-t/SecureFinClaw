---
name: sector-rotation
description: >
  Identify the strongest and weakest sectors by relative strength vs. the SPY benchmark, then
  drill down to the highest-momentum individual stocks within the leading sectors. Use for the
  Sector Rotation Momentum Funnel, Cyclical (Peak Pessimism) Funnel, or any macro-driven
  idea generation.
  Trigger phrases: "sector rotation", "top sectors", "sector momentum", "relative strength",
  "which sectors are leading?", "sector analysis", "macro cycle", "sector vs SPY".
---

# Sector Rotation Analysis

**Your role:** Macro-to-micro momentum analyst. You identify which sectors the market is rewarding
and surface the best individual stock setups within them. This skill bridges `market-regime`
(macro overlay) and `technical-timing` (single-stock entry signal).

---

## Step 1 — Rank Sectors by Relative Strength

```
relative_strength(command="sector_ranking")
```

This ranks all 11 GICS sectors (XLK, XLV, XLF, XLY, XLP, XLE, XLI, XLB, XLRE, XLU, XLC)
by composite relative strength vs SPY across 1M/3M/6M/12M windows.

**Read the output:**
- `top_2` — the two sectors with the highest RS composite. These are your rotation targets.
- `bottom_2` — the two most beaten-down sectors (inputs for the Cyclical / Peak Pessimism funnel).
- `rs_composite` — positive = outperforming SPY; negative = underperforming.

**Macro context check:** Before proceeding, cross-reference with `market-regime` output.
If the regime is "Bear (Crisis)", sector rotation signals are less reliable — momentum
reverses violently in crisis periods.

---

## Step 2 — Find the Top Stock Within Each Leading Sector

For each of the top-2 sector ETFs identified in Step 1:

1. **Source candidate stocks** using the screener:
   ```
   stock_screener(preset="undervalued_growth", limit=20)
   ```
   Or use any other preset appropriate to the sector (e.g., `high_roic_small_cap` for XLK).

2. **Rank by RS vs SPY:**
   ```
   relative_strength(command="top_in_sector", symbols="AAPL,MSFT,NVDA,...", top_n=3)
   ```

3. **Select the single highest-momentum name** from each sector for further analysis.

---

## Step 3 — Momentum Analysis on the Candidate

For each top-sector stock candidate, invoke technical-timing or compute directly:

```
yfinance(command="historical", symbol="<TICKER>", start_date="<6m ago>", end_date="<today>", interval="1d")
```

Check:
- **RSI (14):** Above 60 = strong momentum. Between 50–60 = building.
- **Price vs SMA-50 and SMA-200:** Must be above both for a clean trend.
- **Volume expansion:** Recent volume above 20-day average = institutional accumulation.
- **Leading or lagging its sector:** If the stock's RS > sector ETF RS, it is outperforming
  even within the leading sector — strongest possible setup.

---

## Step 4 — Define the Trade Setup

For the **single best setup** across both candidates:

| Element | Definition |
|---------|-----------|
| **Entry trigger** | RSI pullback to 50–55 on daily chart, or break above recent resistance with volume |
| **Stop-loss** | Below the most recent higher low (or SMA-50 for trailing stop) |
| **Target** | 3:1 risk/reward minimum; project to previous resistance or 1-ATR extension |
| **Catalyst check** | Any earnings in next 3 weeks? Run `earnings_calendar(command="upcoming")` |

---

## Step 5 — Flag Risk Events

```
earnings_calendar(command="upcoming", symbols="<TICKER1>,<TICKER2>", days_ahead=21)
```

If either candidate reports earnings within 3 weeks:
- Reduce position size to 0.5% risk rule (event risk)
- Consider whether you want pre-earnings momentum or post-earnings drift trade

---

## Output — Sector Rotation Card

```
# Sector Rotation Analysis
*Date: [DATE]*  |  Benchmark: SPY

### Sector Rankings (Composite RS)
| Rank | Sector ETF | Sector | RS 1M | RS 3M | RS Composite |
|------|------------|--------|-------|-------|--------------|
| 1    | [XLK]      | Tech   | +X%   | +X%   | +X%          |
| 2    | [...]      | ...    | ...   | ...   | ...          |
| ...  | ...        | ...    | ...   | ...   | ...          |
| 11   | [XLE]      | Energy | −X%   | −X%   | −X%          |

**Macro Regime:** [Bull / Caution / Bear] (from market-regime skill)

### Top Candidates
**Sector 1: [XLK — Technology]**
- Top stock: [TICKER] — RSI [X], RS composite [+X%], volume trend [X]x avg
- Entry trigger: [e.g., "Pullback to $XXX (SMA-50) with RSI reset to 52"]
- Stop-loss: $[XX] (below [support level])
- Target: $[XX]  |  Risk/Reward: [X]:1
- Earnings risk: [None in 3 weeks / Reports [DATE] — flag]

**Sector 2: [XLV — Healthcare]**
- Top stock: [TICKER] — [same format]

### Single Best Setup
**[TICKER]** — [Sector]
> [2–3 sentences: why this is the strongest setup, combining sector leadership + individual stock momentum + entry trigger clarity]

### Position Sizing
1% portfolio risk rule on $100,000 with stop-loss distance as denominator.
```

---

## Cyclical / Peak Pessimism Application

When the user references the Cyclical funnel (buying maximum hate):
- Use `bottom_2` sectors from the ranking as starting points.
- Check if the sector is down >20% (the funnel's filter). Compare `rs_composite` to −20%.
- Find the stock within the beaten-down sector trading at the lowest P/B and EV/EBITDA
  relative to its 10-year history (requires `yfinance info` + manual assessment).
- Cross-reference with `market-regime` to assess cycle timing.

---

## Cross-References
- **relative_strength** tool: upstream data source for all RS calculations
- **market-regime**: mandatory macro overlay before acting on rotation signals
- **technical-timing**: downstream — detailed entry signal after sector candidate identified
- **earnings** skill: check earnings calendar for setup-breaking events
- **bet-sizing**: 1% portfolio risk rule, $100K, sector rotation funnels
