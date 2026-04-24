---
name: bet-sizing
description: "Determine how much capital to allocate to individual positions within a portfolio. Use when the user asks about position sizing, the Kelly criterion, fractional Kelly, risk budgeting, or conviction weighting. Also trigger when users mention 'how much to put in one stock', 'maximum position size', 'how concentrated should my portfolio be', 'number of holdings', 'VaR budget per position', 'how big a bet', or ask about scaling position sizes with volatility."
---

# Bet Sizing

## Purpose
Provides frameworks for determining how much capital to allocate to individual positions within a portfolio. Covers the Kelly criterion, fractional Kelly, risk budgeting, liquidity-based sizing, and conviction weighting. Proper bet sizing is critical — even a portfolio of good ideas can fail with poor sizing.

## Layer
4 — Portfolio Construction

## Direction
prospective

## When to Use
- Determining the appropriate size for a new position
- Applying the Kelly criterion to a bet or investment with estimable odds
- Allocating a risk budget across active positions
- Setting maximum position sizes based on liquidity or risk limits
- Sizing positions proportional to conviction and edge
- Deciding the optimal number of positions in a concentrated portfolio
- Scaling position sizes with volatility changes

## Core Concepts

### Kelly Criterion (Discrete)
For a binary bet with payoff odds b, win probability p, and loss probability q = 1-p:

f* = (b*p - q) / b

where f* is the optimal fraction of wealth to wager. The Kelly criterion maximizes the expected logarithm of wealth (geometric growth rate) over repeated bets.

Properties:
- f* = 0 when edge = 0 (no bet when there is no advantage)
- f* < 0 when negative edge (the formula tells you to bet the other side)
- f* > 0 only when b*p > q (positive expected value)

### Kelly Criterion (Continuous / Investment)
For a normally distributed investment return with expected excess return mu-r_f and variance sigma^2:

f* = (mu - r_f) / sigma^2

This gives the fraction of total wealth to allocate. For example, an asset with 8% expected excess return and 20% volatility: f* = 0.08 / 0.04 = 2.0 (200% of wealth — implying leverage).

### Fractional Kelly
Full Kelly sizing is theoretically optimal but practically too aggressive because:
- It assumes perfect knowledge of probabilities and payoffs
- It produces large drawdowns (the expected drawdown of full Kelly is significant)
- Estimation error in parameters can turn optimal into catastrophic

Practical approach: use a fraction of Kelly, commonly:
- **Half Kelly (f*/2):** Achieves 75% of the growth rate with substantially lower variance and drawdown risk
- **Third Kelly (f*/3):** Even more conservative; appropriate when parameter uncertainty is high
- **Quarter Kelly (f*/4):** Suitable for highly uncertain estimates

The key insight: the growth rate curve is flat near the peak. Reducing from full Kelly to half Kelly only sacrifices 25% of growth but reduces risk dramatically.

### Risk Budgeting
Allocate risk (not capital) across positions. The total risk budget is the maximum acceptable portfolio risk (e.g., 10% VaR or 5% tracking error).

**VaR-based budgeting:**
- Total VaR budget: e.g., $1M at 95% confidence
- Allocate across positions: Position VaR_i <= allocated VaR_i
- Position VaR = w_i * sigma_i * z_alpha * Portfolio Value

**Tracking error budgeting (for active managers):**
- Total active risk budget: e.g., 4% tracking error
- Allocate across bets: each active bet consumes a portion of tracking error
- Size active positions so that sum of risk contributions equals total risk budget

### Maximum Position Sizes
Hard limits on individual positions to prevent concentration risk:

**Liquidity-based limits:**
- Position < X% of average daily volume (ADV) — common limits: 10-25% of ADV
- Ensures ability to exit within a reasonable time frame (e.g., 5-10 trading days)

**Risk-based limits:**
- Position risk contribution < X% of portfolio volatility (e.g., max 10% of portfolio risk)
- Single position < X% of portfolio value (common: 5% for diversified, 10% for concentrated)

**Regulatory/mandate limits:**
- Mutual fund: no more than 5% in a single name (diversified fund) or 25% (non-diversified)
- Index tracking: weight cannot deviate from benchmark by more than specified amount

### Conviction Weighting
Size positions proportional to the strength of the investment thesis:

- **High conviction (largest positions):** Strong edge, deep research, multiple confirming factors
- **Medium conviction:** Solid thesis but some uncertainty or limited information
- **Low conviction (smallest positions):** Early-stage idea, limited edge, or purely diversification-motivated

Framework: Score each position on edge strength (1-5) and certainty (1-5). Size proportional to the product: edge * certainty.

### Optimal Number of Positions
Trade-off between diversification and conviction:

- **Concentrated (10-20 positions):** High conviction, deep research. Each position is 5-10% of the portfolio. Appropriate when the manager has genuine skill and edge.
- **Diversified (50-100 positions):** Lower conviction per position but broader risk reduction. Each position is 1-3%. Appropriate for systematic or factor-based strategies.
- **Very diversified (100+):** Index-like. Risk comes from factor tilts, not individual positions.

### Volatility Scaling
Adjust position sizes inversely with volatility to maintain consistent risk per position:

Adjusted size = Target risk / Current volatility

When volatility doubles, position size halves, keeping the dollar risk constant. This is a core principle in managed futures and risk-targeting strategies.

### Anti-Martingale (Kelly-like) Sizing
Increase position sizes after gains (wealth grows, so Kelly fraction applied to larger base) and decrease after losses. This contrasts with martingale strategies (doubling down after losses) which can lead to ruin.

Kelly naturally implements anti-martingale sizing: bet a constant fraction of current wealth, so absolute bet size grows with wealth and shrinks with losses.

## Reference Material

For full formulas, worked examples, and detailed methodology, read:
`references/detail.md` (in this skill's directory)


## Common Pitfalls
- Full Kelly is too aggressive for practical use — estimation errors in probabilities and payoffs can lead to over-betting and ruin; always use fractional Kelly
- Kelly assumes known probabilities and payoffs — in reality these are estimated with significant error, making full Kelly dangerous
- Kelly maximizes log wealth (geometric growth rate), which may not match an investor's actual utility function or risk tolerance
- Ignoring liquidity constraints: Kelly-optimal size may exceed what the market can absorb without impact
- Correlation between positions: the single-asset Kelly formula does not account for portfolio effects; positions with correlated risk collectively require smaller sizing
- Survivorship bias in parameter estimation: historical win rates may overstate future edge
- Not adjusting for regime changes: edge and volatility are time-varying

## Cross-References
- **value-investing**: valuation-based edge estimates feed into conviction weighting
- **investment-critic**: downstream validation before sizing
- **technical-timing**: upstream — confirms entry timing signal before capital is allocated
- **historical-risk**: realized volatility as a key input to Kelly sizing
- [Not yet implemented] **forward-risk**: expected return forecasts as inputs to Kelly criterion
- [Not yet implemented] **portfolio-construction**: tension between concentration and diversification

---

## Funnel Kelly Presets

Pre-configured Kelly assumptions for each funnel in the FinClaw funnel library.
Use these when the user runs a specific funnel prompt and asks for position sizing.

| Funnel | Win Prob | Payoff Ratio | Max Cap | Portfolio | Risk Rule | Notes |
|--------|----------|-------------|---------|-----------|-----------|-------|
| **Deep Value (Net-Net)** | 55% | 1.5:1 | 15% | $100K | Kelly | Illiquidity premium; hard cap for net-nets |
| **Quality Compounder** | 65% | 3:1 | 25% | $100K | Kelly | High conviction; long hold period |
| **Dividend & Income** | — | — | — | $100K | 2% risk rule | Stop below multi-year support; no Kelly |
| **Turnaround** | 50% | 3:1 | — | $100K | 0.75% risk rule | Binary outcome; fixed risk rule preferred |
| **Cyclical (Peak Pessimism)** | 55% | 2.5:1 | 20% | $100K | Kelly | Medium-high risk; hard cap |
| **Spin-Off & Special Situation** | 60% | 2:1 | — | $100K | Kelly | Medium risk; no hard cap specified |
| **Hidden Champion (Small-Cap)** | 65% | 3:1 | 15% | $100K | Kelly | Smaller float = illiquidity cap |
| **Asset-Heavy / Sum-of-Parts** | 60% | 2:1 | — | $100K | Kelly | Catalyst-dependent |
| **Insider Conviction** | 62% | 2:1 | — | $100K | Kelly | Insider edge premium |
| **GARP** | 60% | 2.5:1 | 20% | $100K | Kelly | Growth-quality balance |
| **ETF Momentum** | — | — | — | $100K | 1.5% risk rule | Stop = support; no Kelly |
| **Sector Rotation** | — | — | — | $100K | 1% risk rule | Stop below recent higher low |
| **Breakout Earnings** | — | — | — | $100K | 0.75% risk rule | Binary event; reduced size |
| **Small-Cap Catalyst** | — | — | — | $100K | 0.75% risk rule | High vol; fixed risk rule |
| **RS Divergence** | — | — | — | $100K | 1% risk rule | Counter-trend; wider stops |
| **Multi-Timeframe** | — | — | — | $100K | 1% risk rule | Tight 4H stop = larger share count |

### Kelly Calculation (for Kelly-based funnels)

```
f* = (b × p − q) / b
where b = payoff ratio, p = win probability, q = 1 − p

Half-Kelly = f* / 2   (recommended for estimated probabilities)
Position size ($) = Half-Kelly × Portfolio Value
Cap at the Max Cap percentage shown above.
```

**Always use Half-Kelly (f* / 2).** Full Kelly assumes perfect probability estimates; half-Kelly
achieves 75% of the growth rate with substantially lower drawdown risk.

### Risk-Rule Sizing (for fixed-risk funnels)

```
Position size ($) = (Portfolio × Risk%) / Stop distance (as fraction of price)
```

Example: 1% risk on $100K portfolio with stop 5% below entry = $2,000 / 5% = $40,000 position.

## Reference Implementation
See `scripts/bet_sizing.py` for computational helpers.
