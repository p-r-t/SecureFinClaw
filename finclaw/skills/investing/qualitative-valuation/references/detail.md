# Qualitative Valuation — Reference Material

## ESG Integration
Material environmental, social, and governance factors that affect long-term value:

- **Environmental:** Carbon emissions, water usage, waste management, climate transition risk
- **Social:** Labor practices, supply chain standards, diversity and inclusion, data privacy, community impact
- **Governance:** Board independence, executive compensation, shareholder rights, audit quality, related-party transactions

## ESG Approaches
Different strategies for incorporating ESG into investment decisions:

- **Negative Screening:** Exclude industries or companies that fail minimum standards (tobacco, weapons, etc.)
- **Positive Screening (Best-in-Class):** Select companies with top ESG ratings within each sector
- **ESG Integration:** Systematically incorporate material ESG factors into valuation (adjust discount rate, growth assumptions, or risk estimates)
- **Impact Investing:** Target measurable positive social or environmental outcomes alongside financial returns

## Industry Life Cycle
Stage of industry evolution affects growth rates, competitive dynamics, and appropriate valuation multiples:

- **Growth:** Rapid adoption, high investment, low/no profits — value on revenue multiples or TAM
- **Maturity:** Stable growth, established players, solid margins — value on earnings or cash flow multiples
- **Decline:** Shrinking market, consolidation, cash harvesting — value on asset basis or liquidation value

## Competitive Positioning
Generic strategies (Michael Porter):

- **Cost Leadership:** Lowest-cost producer, competing on price (Walmart, Costco)
- **Differentiation:** Premium product/service commanding higher margins (Apple, LVMH)
- **Niche/Focus:** Dominate a narrow segment through specialization (ASML, Veeva)

## Key Formulas

| Formula | Expression | Use Case |
|---------|-----------|----------|
| Moat Score | Count of moat sources × durability weight | Aggregate moat strength |
| ROIC vs. WACC | ROIC - WACC (spread) | Economic value creation indicator |
| Five Forces Score | Average intensity across 5 forces (1-5 scale) | Industry attractiveness |
| LTV/CAC | Customer Lifetime Value / Acquisition Cost | Business model efficiency |
| ESG Discount Rate Adj. | r_adjusted = r_base + ESG risk premium | ESG-adjusted valuation |

## Worked Examples

### Example 1: Moat Assessment — Enterprise Software Company
**Given:**
- Cloud-based ERP platform with 95% gross retention, 120% net retention
- Average customer implementation takes 12-18 months
- Data integration with customer systems creates deep embedding
- No network effects; moderate brand value; costs in line with peers

**Calculate:** Moat sources and width

**Solution:**

Moat source analysis:
1. **Switching Costs — STRONG:** 12-18 month implementation, deep data integration, 95% gross retention, and 120% net retention all indicate very high switching costs. Customers are deeply locked in.
2. **Network Effects — ABSENT:** ERP systems do not become more valuable with more users.
3. **Intangible Assets — MODERATE:** Brand is recognized but does not confer meaningful pricing power above peers.
4. **Cost Advantages — ABSENT:** Cost structure is in line with competitors.
5. **Efficient Scale — ABSENT:** Market is large enough to support multiple competitors.

Assessment: **Narrow-to-Wide moat.** Switching costs are the dominant and very strong moat source. The lack of a second reinforcing moat source makes "wide" uncertain, but the depth of customer lock-in (120% net retention) pushes toward wide moat territory. Durability: 15-20+ years, barring a fundamental technology shift.

### Example 2: ESG Integration — Impact on Discount Rate
**Given:**
- Base cost of equity: 9%
- Company operates in a high-carbon industry with no transition plan
- Regulatory risk: pending carbon tax legislation could reduce EBIT by 15%
- Governance: independent board, aligned compensation, no red flags

**Calculate:** ESG-adjusted discount rate

**Solution:**

ESG risk assessment:
- **Environmental risk premium: +1.5%** — High carbon exposure with no transition plan creates material stranded asset and regulatory risk. Pending legislation could impair earnings significantly.
- **Social risk premium: +0.0%** — No material social risk factors identified.
- **Governance risk premium: -0.25%** — Strong governance partially offsets other risks (good governance can lead to better adaptation over time).

ESG-adjusted cost of equity = 9.0% + 1.5% + 0.0% - 0.25% = **10.25%**

Alternatively, instead of adjusting the discount rate, the analyst could model a scenario where EBIT declines 15% due to carbon tax and probability-weight the outcomes. Both approaches capture the ESG risk; the scenario approach is more transparent.
