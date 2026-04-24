"""Position Sizing Tool - calculates trade size based on Kelly Criterion and Portfolio Risk Rules."""

import json
from typing import Any
from pydantic import ConfigDict
from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

class PositionSizingTool(Tool):
    """Calculates suggested position size using Kelly Criterion and Portfolio Risk (e.g. 1% rule)."""

    name = "position_sizer"
    description = (
        "Calculates optimal position sizing. Supports the Kelly Criterion "
        "(based on win probability and payoff ratio) and the fixed Portfolio Risk Rule "
        "(e.g., 1% of account risked based on stop-loss distance)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "method": {
                "type": "string",
                "enum": ["kelly", "risk_rule", "both"],
                "description": "Calculation method. 'kelly' for mathematical optimization, 'risk_rule' for fixed capital at risk.",
                "default": "both"
            },
            "account_value": {
                "type": "number",
                "description": "Total portfolio value (e.g., 100000).",
                "default": 100000
            },
            "entry_price": {
                "type": "number",
                "description": "Planned entry price for the stock."
            },
            "stop_loss": {
                "type": "number",
                "description": "Stop-loss price level."
            },
            "win_probability": {
                "type": "number",
                "description": "Estimated probability of a winning trade (0.0 to 1.0). Required for Kelly.",
                "default": 0.55
            },
            "payoff_ratio": {
                "type": "number",
                "description": "Ratio of average win to average loss (e.g., 2.0 for a 2:1 trade). Required for Kelly.",
                "default": 2.0
            },
            "risk_percent": {
                "type": "number",
                "description": "Percentage of total account to risk on this trade (e.g., 0.01 for 1%). Required for risk_rule.",
                "default": 0.01
            },
            "max_position_cap": {
                "type": "number",
                "description": "Maximum percentage of portfolio allowed for a single position (e.g., 0.20 for 20%).",
                "default": 0.20
            }
        },
        "required": ["entry_price", "stop_loss"]
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self, **kwargs: Any) -> str:
        method = kwargs.get("method", "both")
        account_value = float(kwargs.get("account_value", 100000))
        entry_price = float(kwargs.get("entry_price", 0))
        stop_loss = float(kwargs.get("stop_loss", 0))
        win_prob = float(kwargs.get("win_probability", 0.55))
        payoff = float(kwargs.get("payoff_ratio", 2.0))
        risk_pct = float(kwargs.get("risk_percent", 0.01))
        max_cap = float(kwargs.get("max_position_cap", 0.20))

        if entry_price <= 0 or stop_loss <= 0 or entry_price <= stop_loss:
            return json.dumps({"error": "Invalid price levels. Entry must be greater than stop-loss."})

        results = {"method": method, "inputs": kwargs}

        # 1. Risk-Based Sizing (Fixed Risk Rule)
        # Shares = (Account * Risk%) / (Entry - Stop)
        risk_amount = account_value * risk_pct
        price_risk = entry_price - stop_loss
        risk_shares = int(risk_amount / price_risk) if price_risk > 0 else 0
        risk_capital_required = risk_shares * entry_price
        risk_portfolio_pct = risk_capital_required / account_value

        results["risk_rule"] = {
            "suggested_shares": risk_shares,
            "capital_required": round(risk_capital_required, 2),
            "portfolio_allocation_pct": round(risk_portfolio_pct * 100, 2),
            "amount_at_risk": round(risk_amount, 2),
            "is_capped": risk_portfolio_pct > max_cap
        }
        if results["risk_rule"]["is_capped"]:
            capped_shares = int((account_value * max_cap) / entry_price)
            results["risk_rule"]["capped_shares"] = capped_shares
            results["risk_rule"]["capped_capital"] = round(capped_shares * entry_price, 2)

        # 2. Kelly Criterion
        # Kelly % = (W * R - L) / R  where L = 1 - W
        # We usually use "Half-Kelly" or "Quarter-Kelly" for safety
        loss_prob = 1.0 - win_prob
        full_kelly = (win_prob * payoff - loss_prob) / payoff if payoff > 0 else 0
        
        # Kelly suggests allocation percentage of equity
        half_kelly = full_kelly / 2.0
        
        # Limit by max_cap
        suggested_kelly_pct = min(max(0, half_kelly), max_cap)
        kelly_capital = account_value * suggested_kelly_pct
        kelly_shares = int(kelly_capital / entry_price)

        results["kelly"] = {
            "full_kelly_pct": round(full_kelly * 100, 2),
            "suggested_half_kelly_pct": round(half_kelly * 100, 2),
            "effective_allocation_pct": round(suggested_kelly_pct * 100, 2),
            "suggested_shares": kelly_shares,
            "capital_required": round(kelly_shares * entry_price, 2),
            "win_loss_ratio": payoff
        }

        # Recommendation
        if method == "kelly":
            results["recommendation"] = f"Buy {kelly_shares} shares (Half-Kelly allocation of {results['kelly']['effective_allocation_pct']}%)."
        elif method == "risk_rule":
            rec_shares = risk_shares if not results["risk_rule"]["is_capped"] else results["risk_rule"]["capped_shares"]
            results["recommendation"] = f"Buy {rec_shares} shares (Risking {risk_pct*100}% of portfolio value)."
        else:
            # Conservative: pick the smaller of the two
            final_shares = min(kelly_shares, risk_shares if not results["risk_rule"]["is_capped"] else results["risk_rule"]["capped_shares"])
            results["recommendation"] = f"Conservative Choice: Buy {final_shares} shares."

        return json.dumps(sanitize_json(results), indent=2)
