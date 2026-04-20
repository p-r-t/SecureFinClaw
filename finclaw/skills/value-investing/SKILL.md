---
name: value-investing
description: >
  Perform a deep Pabrai-style "Dhandho" value investing analysis on a specific stock ticker.
  Use this skill when the user provides a ticker and asks to: analyze it for value investing,
  run a Pabrai or Dhandho framework analysis, check FCF yield / P/E / ROE, run a DCF or
  intrinsic value calculation, assess management quality or moat, or ask "is X a good value
  investment?". Also triggers for casual phrasings like "run me through the numbers on TICKER",
  "is this cheap?", or "what do you think of $TICKER".
  IMPORTANT: This skill requires a specific ticker as input. For discovering tickers, use
  the `stock-screener` skill first.
---

# Value Investing — Pabrai "Dhandho" Analysis

Implements the "Heads I win, tails I don't lose much" framework. Requires a ticker as input.
Produces a **structured markdown report** across three stages: Screening → Qualitative Checklist
→ Intrinsic Value & Margin of Safety.

For idea discovery (finding tickers), use the `stock-screener` skill first.
For adversarial red-teaming of the output, follow up with the `investment-critic` skill.

---

## Stage 1 — Fundamental Screening

**Goal:** Filter for simple, high-quality businesses at reasonable prices.

Call `fundamental_scorecard` with `ticker` and `years: 5`:
```
fundamental_scorecard(ticker="TICK", years=5)
```

Then enrich with forward-looking context:
```
earnings_calendar(command="consensus", symbol="TICK")
earnings_calendar(command="revisions",  symbol="TICK")
```

**Pass/Fail criteria (check `.dhandho_flags`):**

| Metric | Target | Flag |
|--------|--------|------|
| P/E ratio | < 15x (ideally < 12x) | `pe_lt_15` |
| FCF Yield | > 6% | `fcf_yield_gt_6pct` |
| 5-yr avg ROE | > 15% consistently | `roe_avg_gt_15pct` |
| Debt / Equity | < 0.5 | `de_lt_0_5` |

**Forward check (from `consensus`):** If forward EPS is declining significantly vs. trailing,
flag as a potential value trap before proceeding. Falling estimates negate a cheap P/E.

**Output:**
```
### 📊 Stage 1: Fundamental Screen — [TICKER]

| Metric       | Value  | Target  | Pass/Fail |
|--------------|--------|---------|-----------||
| P/E          | ...    | < 15x   | ✅ / ❌   |
| FCF Yield    | ...    | > 6%    | ✅ / ❌   |
| 5yr Avg ROE  | ...    | > 15%   | ✅ / ❌   |
| D/E Ratio    | ...    | < 0.5   | ✅ / ❌   |
| Fwd EPS Trend| ...    | Stable/Rising | ✅ / ⚠️ |

**Verdict:** Passes screen / Fails screen (reason)
```

If the stock fails the screen (fewer than 3/4 Dhandho flags), stop here and note why.
Only continue to Stages 2 & 3 if it passes — or the user explicitly requests it.

---

## Stage 2 — Qualitative Checklist

**Goal:** Systematic due diligence against Pabrai's checklist.

**Data sources:**
- Use `sec_edgar_tool` to find the most recent 10-K and 10-Q filings.
- Search for recent earnings call transcripts: `"[TICKER] earnings call transcript Q[N] [YEAR]"`

**Checklist — answer each: Yes / No / Requires Human Review**

**Moat & Business Quality**
- Does the business have a durable competitive advantage (pricing power, switching costs, network effects, or cost advantage)?
- Is this a "painfully simple" business in an industry with an ultra-slow rate of change?
- Are returns on capital consistently high (ROIC > cost of capital for 5+ years)?
- Does the company operate in a large addressable market with room to reinvest?

**Management**
- Is management honest? (No history of misleading disclosures, restatements, or shareholder dilution)
- Is management competent? (Capital allocation skill — buybacks, dividends, acquisitions at sensible prices)
- Are incentives aligned? (Significant insider ownership, sensible comp structure)
- Does the CEO communicate candidly about mistakes?

**Risk Profile**
- Is this a low-risk / high-uncertainty situation? (Market fears are temporary, not structural)
- Is there a clear downside floor? (Assets, cash flows, or liquidation value limits the loss)
- Free of existential risks? (Regulatory, technological disruption, key-man dependency)
- Does the business generate cash in bad years, not just good ones?

**Output:**
```
### ✅ Stage 2: Qualitative Checklist — [TICKER]

| Question | Answer | Evidence |
|----------|--------|----------|
| Durable moat? | Yes | [brief source note] |
...

**Checklist Summary:** X/12 Yes | Y/12 No | Z/12 Requires Human Review
**Qualitative Verdict:** Strong / Borderline / Weak
```

---

## Stage 3 — Intrinsic Value & Margin of Safety

**Goal:** Conservative DCF valuation. Demand a 50% margin of safety.

**CRITICAL RULE:** Do NOT estimate the DCF in your head. Always use native tool calls.

### Step 3a — Run DCF
```
calculate_dcf(
    fcf=<current.fcf_ttm_m>,
    shares=<current.shares_outstanding_m>,
    growth_rate_1_5=<derived.fcf_cagr_pct / 100>,  # convert % to decimal, cap at 0.12
    price=<current.price>
)
```

If `fcf_cagr_pct` is null or negative, use a conservative default of `0.05`.

### Step 3b — Run Sensitivity Matrix
```
valuation_sensitivity(fcf=<fcf_ttm_m>, shares=<shares_outstanding_m>)
```

**Output:**
```
### 💰 Stage 3: Intrinsic Value — [TICKER]

**DCF Inputs**
- Current FCF: $X M | Growth (Yr 1–5): X% | Growth (Yr 6–10): X%
- Discount Rate: 10% | Terminal Multiple: 12x

[Insert markdown_table from valuation_sensitivity result]

**Base Case Intrinsic Value:** $X.XX
**Current Price:** $X.XX
**Margin of Safety:** X%
[Report result.margin_of_safety.verdict]
```

---

## Final Report Structure

```
# Dhandho Value Analysis: [COMPANY] ([TICKER])
*Analysis Date: [DATE]*

## Stage 1: Fundamental Screen        [output]
## Stage 2: Qualitative Checklist     [output]
## Stage 3: Intrinsic Value           [output]

---
## Overall Verdict
**Quantitative:** Pass / Fail
**Qualitative:** Strong / Borderline / Weak
**Valuation:** X% margin of safety (threshold: 50%)

### Investment Thesis (if applicable)
[2–3 sentences: bull case and the single biggest risk]

### Action
- ✅ Warrants further research — consider passing to `investment-critic` for red-teaming
- ❌ Does not meet Dhandho criteria — pass for now
```

---

## Conservative Defaults

| Parameter | Default | Max allowed |
|-----------|---------|-------------|
| Growth Yr 1–5 | 5% | 12% |
| Growth Yr 6–10 | Growth1 / 2 | — |
| Discount rate | 10% | — |
| Terminal multiple | 12x | 15x |
| Margin of safety threshold | 50% | — |
