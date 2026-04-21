# Bet Sizing — Reference Material

## Key Formulas

| Formula | Expression | Use Case |
|---------|-----------|----------|
| Kelly (Discrete) | f* = (b*p - q) / b | Binary bet sizing |
| Kelly (Continuous) | f* = (mu - r_f) / sigma^2 | Investment position sizing |
| Half Kelly | f = f* / 2 | Practical conservative sizing |
| Growth Rate at Kelly | g* = (mu - r_f)^2 / (2*sigma^2) | Maximum geometric growth |
| Growth Rate at f | g(f) = f*(mu - r_f) - f^2*sigma^2/2 | Growth rate for any fraction |
| Volatility-Scaled Size | w = target_risk / sigma_i | Constant risk per position |
| Position VaR | VaR_i = w_i * sigma_i * z_alpha * V | Position-level risk |

## Worked Examples

### Example 1: Kelly Criterion for a Discrete Bet
**Given:**
- Win probability: p = 55%
- Loss probability: q = 45%
- Even-money payoff: b = 1 (win $1 for every $1 wagered)

**Calculate:** Optimal bet size

**Solution:**

f* = (b*p - q) / b = (1 * 0.55 - 0.45) / 1 = 0.10 / 1 = **10%**

Interpretation: Wager 10% of current wealth on each bet. This maximizes long-run geometric growth.

Practical adjustment (half Kelly): f = 10% / 2 = **5%** — achieves 75% of the maximum growth rate with much lower drawdown risk.

Full Kelly expected drawdown: the probability of losing 50% of wealth at some point is substantial. Half Kelly dramatically reduces this tail risk.

### Example 2: Continuous Kelly for an Investment
**Given:**
- Expected excess return (mu - r_f): 8%
- Volatility (sigma): 20%

**Calculate:** Kelly-optimal allocation

**Solution:**

f* = (mu - r_f) / sigma^2 = 0.08 / (0.20)^2 = 0.08 / 0.04 = **2.00 (200%)**

This implies 200% allocation (2x leverage), which is extremely aggressive.

Practical adjustments:
- Half Kelly: 100% (no leverage, fully invested)
- Third Kelly: 67% allocation
- Quarter Kelly: 50% allocation

Given that the 8% expected return and 20% volatility are estimates with significant uncertainty, half Kelly (100%) or less is prudent. The growth rate curve is:
- Full Kelly: g* = 0.08^2 / (2 * 0.04) = 8% per year
- Half Kelly: g(1.0) = 1.0 * 0.08 - 1.0^2 * 0.04/2 = 6% per year (75% of maximum)
- Quarter Kelly: g(0.5) = 0.5 * 0.08 - 0.5^2 * 0.04/2 = 3.5% per year (44% of maximum)
