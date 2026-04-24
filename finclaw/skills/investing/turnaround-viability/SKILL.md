---
name: turnaround-viability
description: >
  Assess whether a distressed or declining company has a credible path to recovery. Use for the
  Turnaround Value Funnel or any situation where the user is analyzing a company that has declined
  significantly, is FCF-negative, or has undergone management/structural changes.
  Trigger phrases: "turnaround thesis", "is this a turnaround?", "recovery potential",
  "new management", "restructuring", "can the business recover?", "turnaround viability",
  "gross margin stabilizing", "operational leverage".
---

# Turnaround Viability Analysis

**Your role:** Turnaround triage analyst. Most broken companies stay broken. Your job is to
distinguish a cyclical trough with a credible fix from a secular decline heading toward
permanent impairment.

**Binary outcome framing:** Turnarounds are high-variance bets. Size conservatively (0.75% risk rule).
The analysis must identify a specific fix, a specific timeline, and a specific management lever.
"It will get better eventually" is not a thesis.

---

## Step 1 — Establish the Extent of Damage

```
yfinance(command="info", symbol="<TICKER>")
yfinance(command="financials", symbol="<TICKER>")
```

Compute:
- **Price decline from 52-week / all-time high:** Target range 50–80% for the Turnaround funnel.
  `pct_from_52w_high` is available directly from `stock_screener(preset="turnaround_candidate")`.
- **FCF status:** Negative or marginally positive?
- **Gross margin trend:** From quarterly financials — stable, improving, or deteriorating?
- **Revenue trend:** YoY decline? Stabilizing?

---

## Step 2 — Score Turnaround Recovery Signals

Count how many of the following 4 signals are present (need ≥ 2 for investable setup):

| Signal | How to Check | Score |
|--------|-------------|-------|
| **New CEO or CFO in last 18 months** | `insider_transactions(command="recent_filings")` or catalyst_scanner management_change events | +1 |
| **Recent asset sale or restructuring announcement** | `catalyst_scanner(command="ticker_catalysts")` — look for Item 1.01/8.01 events | +1 |
| **Gross margins stabilizing or improving (last 2Q)** | `yfinance(command="financials")` quarterly gross profit ÷ revenue trend | +1 |
| **Insider buying > $500K in last 6 months** | `insider_transactions(command="cluster_check", days_back=180, min_insiders=1, min_value_per=500000)` | +1 |

---

## Step 3 — Identify the Specific Fix

A viable turnaround thesis requires **three specifics**:

1. **The Fix:** What exactly is wrong and what is being done?
   - Cost structure (layoffs, facility closures, SG&A cuts)?
   - Balance sheet (debt refinancing, asset sales to reduce leverage)?
   - Product line (SKU rationalization, pricing power restoration)?
   - Revenue (new market, new distribution, regained market share)?

2. **The Timeline:** When will the fix be visible in numbers?
   - Cost cuts: 2–4 quarters
   - Balance sheet repair: 1–3 years (depends on debt maturities)
   - Revenue recovery: industry/cycle dependent

3. **Management's Operational Levers:** Does the leadership team have a demonstrated track
   record of executing the specific type of fix required? Fetch MD&A via:
   ```
   sec_edgar(command="ticker_filings", ticker="<TICKER>")
   sec_edgar(command="fetch_and_parse", filing_url="<most_recent_10K>", include_text=true)
   ```
   Read the MD&A section for management's own explanation of the problem and plan.

---

## Step 4 — Recovery DCF

If 3 years from now the company achieves **80% of its prior peak earnings**:

1. Establish peak EPS (look for the historical best year over the last 7 years).
2. Target EPS at recovery = peak EPS × 0.80.
3. Apply the sector median P/E multiple at that recovery EPS.
4. Discount back 3 years at your required return (e.g., 15%).
5. Compare to current price: **What does the stock return if recovery happens?**

---

## Step 5 — Attack the Thesis

**What is the single scenario most likely to make this a permanent impairment?**

1. **Secular disruption:** Is the industry being structurally disrupted (e.g., physical retail, print media, legacy auto)?
2. **Balance sheet cliff:** Can the company survive long enough for the fix to work?
   Compute: Cash + revolver availability vs. monthly cash burn rate.
3. **Management failure:** New CEO with no relevant turnaround experience in this specific problem type.
4. **Customer concentration / defection:** Are key customers moving to competitors during the turnaround?

---

## Output — Turnaround Viability Card

```
# Turnaround Viability Analysis: [TICKER]
*Date: [DATE]*

### Damage Assessment
- **Price vs. 52w High:** −[X]%  (Target range: −50% to −80%)
- **FCF Status:** [Negative ($XM/quarter) / Marginally Positive / Improving]
- **Gross Margin Trend (last 2Q):** [Declining / Stable / Improving by X bps]
- **Revenue Trend:** [−X% YoY / Stable / Early recovery]

### Recovery Signal Score: [N / 4]
| Signal | Present? | Detail |
|--------|----------|--------|
| New CEO/CFO (18 months) | [Yes / No] | [Name, start date] |
| Asset sale / restructuring | [Yes / No] | [Brief description] |
| Gross margin stabilizing | [Yes / No] | [Q data] |
| Insider buying > $500K | [Yes / No] | [Who, how much] |

### The Specific Fix
- **What is broken:** [1 sentence]
- **The fix:** [1 sentence — specific operational lever]
- **Timeline:** [X–Y quarters for first evidence / X–Y years for full recovery]
- **Management's track record for this fix:** [Relevant / Not demonstrated / Unknown]

### Recovery DCF (80% of Peak Earnings in 3 Years)
- Peak EPS: $[X] (year [YYYY])
- Recovery Target EPS: $[X]
- Applied P/E: [X]x
- Implied 3Y Price: $[X]
- Current Price: $[X]
- **Implied 3Y Return: [+X]%  ([X]% CAGR)**

### Permanent Impairment Risk
**Most credible bear case:** [1–2 sentences on the specific scenario that makes this a zero]
**Survival runway:** [X months at current burn rate]
**Assessment:** [CYCLICAL TROUGH / SECULAR DECLINE / UNCLEAR]

### Verdict
**[INVESTABLE TURNAROUND / NEEDS MORE EVIDENCE / AVOID — SECULAR DECLINE]**
[2–3 sentences with specific triggers to re-evaluate if "Needs more evidence"]
```

---

## Cross-References
- **stock-screener** `turnaround_candidate` and `drawdown_50_80`: upstream screening
- **insider-conviction**: validate the insider buying signal
- **catalyst_scanner**: detect management changes and restructuring events
- **investment-critic**: mandatory red-team before committing capital
- **bet-sizing**: 0.75% portfolio risk rule on $100K given binary outcome risk
