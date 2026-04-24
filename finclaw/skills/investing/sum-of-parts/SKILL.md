---
name: sum-of-parts
description: >
  Perform a sum-of-parts (SOTP) or net asset value (NAV) valuation — independently appraising each
  major business segment or asset category and summing to derive intrinsic value. Use for the
  Spin-Off & Special Situation funnel, Asset-Heavy / Sum-of-Parts funnel, or any conglomerate where
  the market price doesn't reflect the value of individual parts.
  Trigger phrases: "sum of parts", "SOTP", "NAV valuation", "conglomerate discount",
  "asset appraisal", "break-up value", "spin-off valuation", "what are the parts worth?".
---

# Sum-of-Parts (SOTP) Valuation

**Your role:** Forensic appraiser. The market is pricing the whole. Your job is to independently
value each piece and determine whether the total is worth more than the current enterprise value.

---

## Step 1 — Map the Business Segments

```
yfinance(command="financials", symbol="<TICKER>")
sec_edgar(command="ticker_filings", ticker="<TICKER>")
```

Then fetch the most recent 10-K using `fetch_and_parse` with `include_text=true` to access
the business overview and segment financials.

Identify:
- How many distinct reportable segments does the company have?
- What revenue and EBIT does each segment contribute?
- What are the primary assets (real estate, energy reserves, equipment, IP, cash)?

---

## Step 2 — Value Each Segment / Asset

For each segment, choose the most appropriate methodology:

### 2a — Revenue/EBITDA Multiple (Operating Businesses)
```
Segment_EV = Segment_EBITDA × Sector_Median_EV/EBITDA_Multiple
```

Look up comparable pure-play companies or sector medians:
- Technology: 15–25x EBITDA
- Industrials: 8–12x EBITDA
- Energy: 4–7x EBITDA
- Real Estate: use NAV/cap-rate approach instead
- Consumer: 10–15x EBITDA
- Finance: P/B or P/E multiple

State your multiple assumption and the comparable set explicitly.

### 2b — NAV / Replacement Cost (Hard Assets)
For real estate, energy reserves, infrastructure:
```
Asset_NAV = Appraised_Value or (Annual_Income / Cap_Rate)
```

For energy reserves: PV-10 (10% discount rate applied to proved reserves cash flows).

### 2c — Cash and Investments
Mark at face value or market value. Subtract any pension deficits or environmental liabilities.

---

## Step 3 — Derive Intrinsic Value

```
SOTP_EV = Sum of all segment EVs + Corporate_Assets − Corporate_Liabilities

SOTP_Equity_Value = SOTP_EV − Net_Debt − Minority_Interest − Pension_Deficit

SOTP_Per_Share = SOTP_Equity_Value / Shares_Outstanding
```

**Discount to SOTP:**
```
Discount = (SOTP_Per_Share − Current_Price) / SOTP_Per_Share × 100
```

---

## Step 4 — Analyze the Discount

A discount to SOTP is only interesting if it can close. Assess:

1. **Capital allocation quality:** Does management reinvest efficiently, or do they destroy value
   faster than the segments generate it?
2. **Structural liability:** Is there a pension deficit, asbestos liability, or regulatory issue
   that rationally explains the discount?
3. **Catalyst to close:** Asset sale, activist pressure, strategic review, spin-off, or sector
   re-rating? Assign a probability and timeline.

**Attack the gap:** What keeps institutional buyers away? Is this:
- Complexity / low analyst coverage? (Edge opportunity)
- Genuine value destruction? (Not investable)
- Forced selling / index exclusion? (Temporary, recoverable)

---

## Step 5 — Spin-Off Specific Analysis

If the subject is a recently spun entity, additionally assess:

```
spin_tracker(command="spin_profile", filing_url="<form_10_url>")
```

- **Rationale:** Was the separation strategically motivated (focus) or dumping a bad business?
- **Equity incentives:** Does management have meaningful equity aligned with the new entity?
- **Forced selling:** Are parent-company shareholders mismatched with the new business?
- **Cleaner balance sheet:** Post-spin debt load vs. pre-spin allocation.

---

## Output — SOTP Valuation Card

```
# Sum-of-Parts Valuation: [TICKER / COMPANY]
*Date: [DATE]*

### Segment Breakdown
| Segment | Revenue | EBITDA | Multiple | Implied EV |
|---------|---------|--------|----------|------------|
| [A]     | $XM     | $XM    | Xx       | $XM        |
| [B]     | $XM     | $XM    | Xx       | $XM        |
| Corporate / Other | — | — | — | ($XM) |

### SOTP Summary
- **Gross SOTP EV:** $XM
- **Net Debt / Liabilities:** ($XM)
- **SOTP Equity Value:** $XM
- **SOTP Per Share:** $XX
- **Current Price:** $XX
- **Discount to SOTP:** [X]%

### Gap Analysis
**Catalyst to close:** [Asset sale / Activist / Spin-off / Sector re-rating]
**Timeline:** [X–Y months]
**Probability:** [X]%

**Why the discount exists:** [1–2 sentences]
**Attack:** [Most credible risk that keeps it depressed]

### Verdict
[BUY THE DISCOUNT / WAIT FOR CATALYST / VALUE TRAP]
[2–3 sentences]
```

---

## Cross-References
- **spin_tracker**: upstream — surface recently spun entities eligible for this analysis
- **investment-critic**: downstream — red-team the SOTP assumptions
- **bet-sizing**: downstream — Kelly Criterion with 60% win prob, 2:1 payoff, $100K portfolio
- **technical-timing**: check whether stock is in confirmed downtrend before committing capital
- **stock-screener**: use presets `asset_heavy_discount` or `net_net` to generate candidates
