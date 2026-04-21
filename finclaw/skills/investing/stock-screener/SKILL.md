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
- Include only **equity positions** (the `equity` array in the response — ignore `options` and `bonds`).
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

## Step 2 — Fundamental Screening

If the user wants initial ideas from pre-screened universes instead of 13Fs, use the `stock_screener` tool. This tool returns up to 20 matched tickers per preset. 

**Available Presets:**
- `dhandho` (Default) — Screen for undervalued growth / high ROE
- `deep_value` — Screen for extreme undervaluation
- `large_cap_value` — Screen for large undervalued companies

```
stock_screener(preset="dhandho", limit=5)
```
You can use `stock_screener` to enrich your watchlist if Step 1 (13F clones) yields fewer than 3 candidates. It operates in bulk so it will not cause rate limit issues.

---

## Step 4 — 52-Week Low Hunt (Optional)

If the user asks to "find quality companies near their lows":

For each ticker in the relevant curated universe, call:
```
yfinance(command="info", symbol="TICK")
```

From the result, extract `fiftyTwoWeekLow` and `currentPrice` (or `regularMarketPrice`), then:
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

## Common Pitfalls

- **13F filing lag**: Filings have a 45-day disclosure delay. Superinvestors may have already sold. Treat as directional signal, not real-time.
- **Survivorship bias in screeners**: Screeners exclude delisted companies, making historical backtests look better than reality.
- **Low P/E ≠ cheap**: A stock with P/E of 5x and declining revenue is not cheap — it's pricing in earnings collapse. Always cross-check with FCF yield and forward estimates.
- **Small sample bias in 13F cloning**: A position appearing in only 1 filing could be a hedge, not a conviction bet. Require 2+ managers for "High Conviction" labeling.
- **Sector concentration**: If the screener returns 5 energy stocks, you don't have diversification — you have a sector bet. Flag sector concentration explicitly.

## Cross-References
- **value-investing**: Downstream — deep analysis on screened candidates
- **earnings**: Enrichment — upcoming earnings dates for watchlist tickers

## Notes

- **Performance:** `fundamental_scorecard` is one API call per ticker and does NOT support
  batching. Call sequentially and cap at 10 tickers per run to stay responsive.
- **Data lag:** 13F filings have a 45-day disclosure delay — treat as directional, not real-time.
- **Not a buy signal:** The watchlist is an idea source only. Always follow up with
  `value-investing` and `investment-critic` before making a decision.
