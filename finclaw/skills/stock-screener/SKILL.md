---
name: stock-screener
description: >
  Screen a universe of stocks to surface cheap, high-quality investment ideas using value-investing
  criteria. Use this skill when the user asks to: find undervalued stocks, screen for cheap
  companies, generate a watchlist, scan an industry or index, identify Pabrai/Dhandho-style
  opportunities, clone Superinvestor 13F filings to discover new ideas, look for stocks with low
  P/E or high FCF yield, find 52-week lows among quality businesses, or says "find me something
  to invest in". Outputs a ranked watchlist — not a full valuation. Use the `value-investing`
  skill to go deep on any resulting ticker.
---

# Stock Screener — Idea Generation

**Goal:** Build a curated watchlist of value candidates. This skill generates ideas.
It does NOT produce a valuation or verdict — pass results to `value-investing` for that.

---

## Step 0 — Determine the Universe

Ask the user which universe to scan if not specified:

| Source | When to use |
|--------|-------------|
| **13F Cloning** | "Find what Superinvestors are buying" |
| **User-provided list** | User gives explicit tickers or a sector |
| **Curated sector lists** (see below) | "Find cheap consumer staples / energy / financials" |
| **52-week low hunt** | "Find quality companies near their lows" |

Default: **13F Cloning + one curated sector list** if the user gives no guidance.

---

## Step 1 — 13F Clone Discovery

Pull new buys and significant increases from Superinvestor filings using `get_13f_holdings`
with `compare_previous: true`.

**Expanded Manager List (use all by default):**

| Manager | Fund | CIK |
|---------|------|-----|
| Warren Buffett | Berkshire Hathaway | `0001067983` |
| Seth Klarman | Baupost Group | `0001061768` |
| Li Lu | Himalaya Capital | `0001709323` |
| Guy Spier | Aquamarine Fund | `0001159165` |
| Bill Ackman | Pershing Square | `0001336528` |
| David Einhorn | Greenlight Capital | `0001079114` |
| Joel Greenblatt | Gotham Asset Mgmt | `0001328835` |
| Chuck Akre | Akre Capital Mgmt | `0001112520` |

**Rules:**
- Include only **equity positions** (`current_holdings`, not `options_positions` or `bond_positions`).
- Flag positions appearing in **2+ filings** as **High Conviction**.
- Flag positions that are **new** (not in previous filing) as **New Buy**.
- Flag positions increased **> 20%** in share count as **Significant Add**.

**Output table:**
```
| Ticker | Company | Manager(s) | Action | Conv. Level |
|--------|---------|------------|--------|-------------|
| KO     | Coca-Cola | Buffett | Significant Add | High |
```

---

## Step 2 — Fundamental Pre-Screen

For each candidate from Step 1 (cap at 20 tickers to stay performant), call:
```
fundamental_scorecard(ticker="TICK", years=3)
```

Use batch calls where possible. Check the `dhandho_flags` object for quick pass/fail:

| Flag | Criterion | Required for pass |
|------|-----------|-------------------|
| `pe_lt_15` | P/E < 15x | ✅ Must pass |
| `fcf_yield_gt_6pct` | FCF Yield > 6% | ✅ Must pass |
| `roe_avg_gt_15pct` | 5yr avg ROE > 15% | ✅ Must pass |
| `de_lt_0_5` | D/E < 0.5 | 🔶 Preferred, not disqualifying |

**Pass threshold:** At least 3 of 4 flags. Discard anything with fewer than 2.

---

## Step 3 — Sector-Based Scanning (if user requests or no 13F candidates pass)

Use pre-defined curated universes. For each list, call `fundamental_scorecard` per ticker and
apply the same 3/4 flag threshold.

**Curated Universes (Dhandho-friendly sectors):**

```
Consumer Staples:  KO, PG, CL, MKC, CHD, UL, NSRGY, KHC, GIS, SJM
Energy (Majors):   CVX, XOM, COP, OXY, PSX, VLO, MPC, PBF, HES, EOG
Financials:        BRK.B, JPM, BAC, WFC, TRV, ALL, CB, AIG, MET, PRU
Healthcare:        JNJ, ABT, MDT, BDX, ANTM, HUM, CI, CVS, MCK, AHS
Industrials:       MMM, ITW, GD, RTX, HII, LMT, NOC, EMR, PH, ROK
```

Only scan a sector if the user asks for it, or if 13F candidates are sparse.

---

## Step 4 — 52-Week Low Hunt (Optional)

If the user asks to "find quality companies near their lows":

For each ticker in the relevant curated universe, call `get_stock_info` and compute:
```
proximity_to_low = (current_price - fifty_two_week_low) / fifty_two_week_low
```

Flag any ticker where `proximity_to_low < 0.15` (within 15% of 52-week low) AND
`roe_avg_gt_15pct` passes. These are the highest-priority candidates for deep value review.

---

## Output — Ranked Watchlist

Assemble a single table ranked by number of Dhandho flags passed:

```
## 📋 Value Watchlist — [DATE]

| Rank | Ticker | Company | Source | P/E | FCF Yield | ROE | D/E | Flags | Action |
|------|--------|---------|--------|-----|-----------|-----|-----|-------|--------|
| 1    | KO     | Coca-Cola | 13F + Screen | 22x | 6.8% | 38% | 0.4 | 3/4 | ▶ Analyze |
| 2    | CVX    | Chevron   | Screen       | 12x | 9.1% | 16% | 0.2 | 4/4 | ▶ Analyze |

**High Conviction (2+ managers):** KO, OXY
**New Buys this quarter:** AAPL, MCK

*Pass top candidates to `value-investing` for full Dhandho analysis.*
```

Always end with: _"Run `value-investing` on [TICKER] for a full thesis and DCF valuation."_

---

## Notes

- **Performance:** `fundamental_scorecard` is one API call per ticker. Cap the screened universe
  at 20 tickers per run to stay responsive.
- **Data lag:** 13F filings have a 45-day disclosure delay — treat as directional, not real-time.
- **Not a buy signal:** The watchlist is an idea source only. Always follow up with
  `value-investing` and `investment-critic` before making a decision.
