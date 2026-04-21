# Historical Risk — Reference Material

## Key Formulas

| Formula | Expression | Use Case |
|---------|-----------|----------|
| Annualized Volatility | sigma_ann = sigma_period * sqrt(N) | Convert period vol to annual vol |
| Log Return | r_t = ln(P_t / P_{t-1}) | Compute continuously compounded returns |
| Parkinson Variance | sigma^2 = (1 / (4n ln2)) * sum(ln(H/L)^2) | Volatility from high-low data |
| Drawdown | DD_t = (Peak_t - Value_t) / Peak_t | Measure peak-to-trough decline |
| Max Drawdown | MDD = max(DD_t) | Worst historical decline |
| Historical VaR (95%) | 5th percentile of return series | Non-parametric loss estimate |
| Downside Deviation | sigma_d = sqrt((1/n) * sum(min(R_i - MAR, 0)^2)) | Asymmetric risk below MAR |
| Tracking Error | TE = std(R_p - R_b) * sqrt(N) | Portfolio vs benchmark deviation |
| Semi-Variance | (1/n) * sum(min(R_i - mean(R), 0)^2) | Below-mean variance |

## Worked Examples

### Example 1: Annualized Volatility from Daily Returns
**Given:** A stock has daily log returns with a sample standard deviation of 1.2%. Assume 252 trading days per year.

**Calculate:** Annualized volatility.

**Solution:**

```text
sigma_annual = 0.012 * sqrt(252)
             = 0.012 * 15.875
             = 0.1905
             ~ 19.05%
```

The stock's annualized volatility is approximately 19%.

### Example 2: Maximum Drawdown from a Price Series
**Given:** A fund's NAV follows this path over six months: $120, $135, $150, $130, $105, $125.

**Calculate:** Maximum drawdown and identify the peak and trough.

**Solution:**

Running peaks: $120, $135, $150, $150, $150, $150.

Drawdowns at each point:
- $120: (120-120)/120 = 0%
- $135: (135-135)/135 = 0%
- $150: (150-150)/150 = 0%
- $130: (150-130)/150 = 13.3%
- $105: (150-105)/150 = 30.0%
- $125: (150-125)/150 = 16.7%

**Maximum Drawdown = 30.0%**, occurring from the peak of $150 to the trough of $105. As of the last observation ($125), the drawdown has not yet fully recovered.

### Example 3: Historical VaR
**Given:** 500 daily returns sorted from worst to best. The 25th-worst return is -2.8% and the 26th-worst is -2.6%.

**Calculate:** 95% 1-day historical VaR.

**Solution:**

The 5th percentile corresponds to the 25th observation out of 500 (500 * 0.05 = 25).

```text
VaR_95% = -(-2.8%) = 2.8%
```

Interpretation: On 95% of days, the loss is expected not to exceed 2.8% based on the historical distribution.
