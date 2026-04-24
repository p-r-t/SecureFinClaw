---
name: dividend-safety
description: >
  Analyze the safety and sustainability of a company's dividend. Use when the user runs the
  Dividend & Income Value Funnel or asks about dividend safety, FCF coverage, payout ratio
  stress tests, yield-trap detection, or balance sheet risk for income stocks.
  Trigger phrases: "is the dividend safe?", "FCF coverage", "payout ratio stress", "yield trap",
  "dividend sustainability", "can they maintain the dividend?".
---

# Dividend Safety Analysis

**Your role:** Income sustainability analyst. A high yield is not attractive if it signals distress.
Your job is to determine whether the dividend is safe, growing, and backed by real cash flows —
or whether it is a value trap dressed as income.

---

## Step 1 — Gather Data

```
yfinance(command="info", symbol="<TICKER>")
yfinance(command="financials", symbol="<TICKER>")
```

Extract from the results:
- `dividend_yield` — current yield (flag if > 7%: may signal distress)
- `free_cashflow` — trailing 12M FCF
- `total_revenue` — for stress-test baseline
- `total_debt`, `operating_cashflow`
- From financials: dividends paid (cash flow statement), annual EPS

Also call:
```
earnings_calendar(command="consensus", symbol="<TICKER>")
```
to get forward EPS and revenue estimates.

---

## Step 2 — FCF Coverage Ratio

**Formula:**

```
FCF_Coverage = Free_Cash_Flow / Dividends_Paid
```

| Coverage | Interpretation |
|----------|----------------|
| ≥ 2.0x   | Excellent — dividend well protected |
| 1.5–2.0x | Good — comfortable headroom |
| 1.0–1.5x | Adequate — limited buffer |
| < 1.0x   | At Risk — dividend exceeds FCF |

**Payout ratio (earnings-based):**
```
Payout_Ratio = Dividends_Per_Share / EPS
```
Flag if > 65%.

---

## Step 3 — FCF Stress Test

Simulate a **−20% revenue decline** (recessionary scenario):

1. Reduce revenue by 20%.
2. Estimate gross profit at the same margin percentage.
3. Estimate operating income: apply same operating leverage ratio as historical.
4. Estimate stressed FCF = stressed operating income × historical (FCF / Operating Income) ratio.
5. Check if stressed FCF still covers the dividend.

**Verdict:**
- "Dividend survives stress scenario" or "Dividend at risk under −20% revenue scenario"

---

## Step 4 — Balance Sheet Refinancing Risk

From `total_debt` and `financials` balance sheet:

1. Identify any **debt maturities in the next 3 years** (check notes if available, else flag as "data requires 10-K review").
2. Compare current operating cash flow to annual debt service + dividend payments.
3. Flag if debt/EBITDA > 3x: refinancing could compete with dividend.

---

## Step 5 — Yield Trap Check (Attack the Yield)

A high yield can be a trap if the price collapsed on a structural problem:

1. Check 1-year and 3-year price performance.
2. Check revenue and EPS trend: growing, flat, or declining?
3. Check if dividend has been cut in the last 5 years (look for step-downs in yfinance historical dividends).
4. **Red flags:** yield > 7% + declining revenue + P/E compression = likely yield trap. State explicitly.

---

## Step 6 — Dividend Growth Streak

From yfinance historical data or consensus:
- Has the dividend grown for 5+ consecutive years? (Signal of financial health)
- What is the CAGR of dividend growth over 3 and 5 years?

---

## Output — Dividend Safety Card

```
# Dividend Safety Analysis: [TICKER]
*Date: [DATE]*

### Core Metrics
- **Yield:** [X]%  [Normal / High (>5%) / Danger Zone (>7%)]
- **FCF Coverage:** [X]x  [Excellent / Good / Adequate / At Risk]
- **Payout Ratio (EPS):** [X]%  [Safe (<65%) / Elevated / Danger Zone (>85%)]
- **Dividend Growth Streak:** [N] consecutive years  |  5Y CAGR: [X]%

### FCF Stress Test (−20% Revenue)
- Stressed FCF: $[X]M
- Stressed FCF Coverage: [X]x
- **Verdict:** [Survives / At Risk / Fails]

### Balance Sheet Risk
- Net Debt/EBITDA: [X]x
- Major debt maturities (next 3 years): [Yes/No/Needs 10-K review]
- **Refinancing risk:** [Low / Medium / High]

### Yield Trap Assessment
**[SAFE INCOME / WATCH / YIELD TRAP]**
[2–3 sentences explaining the verdict]

### Entry Note
[Comment on whether the stock is near historical yield support — i.e., has the market already priced in the risk, creating a margin of safety?]
```

---

## Cross-References
- **bet-sizing**: downstream — size using 2% portfolio risk rule with stop below multi-year support
- **technical-timing**: upstream — check whether yield is near historical support (entry timing)
- **investment-critic**: use to red-team the dividend thesis before buying
- **stock-screener**: use preset `dividend_safety` to generate initial candidates
