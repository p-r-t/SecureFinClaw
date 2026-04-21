---
name: earnings
description: >
  Look up earnings dates, EPS/revenue beat-or-miss history, forward analyst consensus estimates,
  and estimate revision trends for US and global stocks. Use when the user asks: when a company
  reports earnings, whether they beat or missed, what analysts expect this quarter, whether
  estimates have been raised or cut, or for an upcoming earnings calendar across a watchlist.
  Trigger for phrases like "when does X report?", "did NVDA beat?", "earnings this week",
  "what's the EPS estimate?", "are analysts bullish on X?".
---

# Earnings Calendar & Surprise Tracking

**Data source:** Yahoo Finance (yfinance). Best coverage for US large-caps and major global stocks.

---

## Quick Reference

| Intent | Command | Key params |
|--------|---------|------------|
| Next earnings date | `calendar` | `symbol` |
| Beat/miss history | `surprise` | `symbol`, `limit` |
| Forward EPS/revenue estimates | `consensus` | `symbol` |
| Estimate revision trend | `revisions` | `symbol` |
| Upcoming earnings for a watchlist | `upcoming` | `symbols`, `days_ahead` |

---

## When does X report?

```
earnings_calendar(command="calendar", symbol="AAPL")
```

Report: next date, time (BMO/AMC), EPS estimate range (low/avg/high), revenue estimate.

---

## Did X beat last quarter? / Show earnings history

```
earnings_calendar(command="surprise", symbol="NVDA", limit=8)
```

Format as a table:

| Quarter | EPS Est | EPS Actual | Surprise % | Beat/Miss |
|---------|---------|------------|------------|-----------|

Summarise: _"Beat in 7 of the last 8 quarters (87.5% beat rate)."_

---

## What are analysts expecting this quarter?

```
earnings_calendar(command="consensus", symbol="MSFT")
```

Report: EPS (avg/low/high), YoY growth, revenue estimate, analyst count, recommendation.

---

## Have analysts been raising or cutting estimates?

```
earnings_calendar(command="revisions", symbol="META")
```

Interpret:
- `up_last_30_days > down_last_30_days` → positive revision momentum
- `down_last_30_days > up_last_30_days` → negative trend — flag for the user
- Compare `eps_trend.current` vs `eps_trend.90daysAgo` to show estimate drift magnitude

---

## Upcoming earnings for a watchlist

```
earnings_calendar(command="upcoming", symbols="AAPL,MSFT,NVDA,AMZN,TSLA,META,GOOGL", days_ahead=7)
```

Group results by date. For each: ticker, report date, BMO/AMC, EPS estimate.

**Performance note:** `upcoming` makes one API call per ticker. Keep lists to ≤ 30 symbols.

---

## Integration with Value Investing

After running a `fundamental_scorecard` for a ticker, call `consensus` and `surprise` to enrich
the analysis with forward estimates and beat-rate history. This feeds Stage 2 of the Dhandho
framework — understanding whether the business is meeting or beating expectations.

---

## Notes

- If a ticker returns `"error": "No earnings calendar available"` → likely a non-US stock, ETF,
  SPAC, or thinly-traded name not covered by Yahoo Finance.
- `surprise` only shows **reported** quarters — future dates appear in `calendar`, not `surprise`.
- BMO = Before Market Open · AMC = After Market Close
