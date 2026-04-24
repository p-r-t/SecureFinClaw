---
name: insider-conviction
description: >
  Analyze insider buying activity from SEC Form 4 filings to assess management conviction.
  Use when the user asks about insider buying signals, cluster insider purchases, 10b5-1 plan
  classification, or wants to validate an investment thesis using insider behavior.
  Trigger phrases: "insider buying", "cluster insiders", "Form 4", "management conviction",
  "insiders buying", "10b5-1", "is insider buying real?", "insider activity", "insider signal".
---

# Insider Conviction Analysis

**Your role:** Signal validator. Insider buying is one of the highest-signal data points in equity
research — executives and directors are staking personal capital on the company's prospects.
Your job is to determine whether the buying is genuine conviction or defensive optics.

**Philosophy:** Open-market insider purchases above $100K, from 3+ distinct insiders within 60 days,
excluding 10b5-1 plan transactions, are statistically meaningful. Below that threshold, treat with
skepticism.

---

## Step 1 — Detect Cluster Buying

```
insider_transactions(command="cluster_check", ticker="<TICKER>", days_back=60, min_insiders=3, min_value_per=100000)
```

Assess the output:
- **cluster_detected:** Was the threshold met?
- **qualifying_insiders:** Who bought, and how much? Are these executives or directors?
  (Director buying is good; CEO/CFO buying is the strongest signal.)
- **signal_integrity_warning:** Did any buying insiders also sell in the prior 12 months?
  If yes, the buying may be selective signaling rather than full conviction.

---

## Step 2 — Full Transaction History

```
insider_transactions(command="insider_history", ticker="<TICKER>", days_back=180)
```

Review:
- **open_market_buys vs. sells ratio:** Net buying is positive; net selling alongside buying dilutes the signal.
- **10b5-1 buys excluded:** Pre-planned transactions are scheduled months in advance and do not
  reflect real-time conviction. Only open-market buys count.
- **Pattern of buying:** Is this the first buy, or part of a sustained accumulation?

---

## Step 3 — Fundamental Validation

The insider signal must align with a credible fundamental thesis. Run:

```
yfinance(command="info", symbol="<TICKER>")
yfinance(command="financials", symbol="<TICKER>")
```

Ask: **At the insider's purchase price, what earnings trajectory makes their buy fair value?**

Perform a reverse DCF:
- Assume the insider's average purchase price = fair value.
- Back out the implied EPS growth rate and terminal multiple.
- Is that growth trajectory realistic given current fundamentals?

If the implied growth is unrealistically high, the buying may be optics rather than conviction.

---

## Step 4 — Distress Check

Insider buying during distress is different from buying during a normal pullback:

1. Is the stock down 25%+ from its 52-week high? ← Funnel threshold
2. Is the company FCF positive? Or burning cash?
3. Net debt < 2x EBITDA? If over-levered, insider buying may not overcome balance sheet risk.

---

## Step 5 — Attack the Signal

Before accepting the thesis, challenge it:

1. **Are the buyers credible?** Insider purchases by the Chairman or founder carry more weight
   than a minor director fulfilling a board requirement.
2. **Did they sell recently?** A purchase after recent sales looks like optics.
3. **Is the buy meaningful relative to their wealth?** A $100K buy from a CEO paid $10M/year
   is noise. A $2M buy from a CEO paid $1M/year is a strong signal.
4. **Are there structural reasons insiders can't buy?** Blackout windows, ongoing investigations,
   or pending transactions can explain absence of buying despite insider confidence.

---

## Output — Insider Conviction Card

```
# Insider Conviction Analysis: [TICKER]
*Date: [DATE]*

### Cluster Buying Summary
- **Cluster Detected:** [Yes / No]
- **Distinct Buyers:** [N] insiders  |  Total Purchased: $[X]M
- **Window:** Last [N] days
- **10b5-1 Plans Excluded:** Yes

### Top Buyers
| Name | Title | Date | Shares | Value | Open Market? |
|------|-------|------|--------|-------|--------------|

### Signal Integrity
- **Prior-year sellers among buyers:** [Yes: names / No]
- **Buy/sell ratio (180d):** [N buys / N sells]
- **Signal strength:** [STRONG / MODERATE / WEAK / OPTICS]

### Implied Earnings Trajectory (Reverse DCF at Purchase Price)
- **Insider avg. purchase price:** $XX
- **Implied EPS growth (5Y):** [X]%
- **Realistic?** [Yes / Aggressive / Unrealistic]

### Fundamental Check
- **Net debt/EBITDA:** [X]x  [Safe / Elevated / Danger]
- **FCF status:** [Positive ($XM) / Negative / Marginal]
- **Stock vs 52w high:** −[X]%

### Verdict
**[HIGH CONVICTION BUY SIGNAL / MODERATE SIGNAL / OPTICS / NO SIGNAL]**
[2–3 sentences explaining the verdict and what would make the signal stronger]
```

---

## Cross-References
- **insider_transactions** tool: upstream data source for all insider transaction data
- **value-investing**: validate the fundamental thesis the insider is presumably betting on
- **investment-critic**: downstream red-team to find the disconfirming case
- **bet-sizing**: Kelly with 62% win probability and 2:1 payoff for $100K portfolio
- **stock-screener**: filter candidates by stock-down-25%-from-52w-high + net-debt < 2x EBITDA
