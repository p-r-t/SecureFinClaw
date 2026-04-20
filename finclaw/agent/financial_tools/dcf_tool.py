"""Discounted Cash Flow (DCF) pricing tool."""

import json
from typing import Any
from pydantic import ConfigDict
from loguru import logger

from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

class DCFTool(Tool):
    """Calculates the Intrinsic Value using a two-stage Discounted Cash Flow model."""

    name = "calculate_dcf"
    description = (
        "Calculates the two-stage DCF intrinsic value. "
        "Projects free cash flows over 10 years, discounts them to present value, "
        "and calculates a terminal value. Includes margin of safety check."
    )
    parameters = {
        "type": "object",
        "properties": {
            "fcf": {
                "type": "number",
                "description": "Current Free Cash Flow (total, in millions)."
            },
            "shares": {
                "type": "number",
                "description": "Shares outstanding (in millions)."
            },
            "growth_rate_1_5": {
                "type": "number",
                "description": "Annual growth rate for years 1-5 (e.g. 0.08 for 8%).",
                "default": 0.05
            },
            "growth_rate_6_10": {
                "type": "number",
                "description": "Annual growth rate for years 6-10 (default: half of years 1-5)."
            },
            "discount_rate": {
                "type": "number",
                "description": "Discount rate / hurdle rate (e.g. 0.10 for 10%).",
                "default": 0.10
            },
            "terminal_multiple": {
                "type": "number",
                "description": "Exit multiple to apply to year 10 FCF.",
                "default": 12
            },
            "price": {
                "type": "number",
                "description": "Current market price per share for margin of safety check."
            }
        },
        "required": ["fcf", "shares"]
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def execute(self, **kwargs: Any) -> str:
        fcf = kwargs.get("fcf")
        shares = kwargs.get("shares")
        if fcf is None or shares is None:
            return json.dumps({"error": "Both 'fcf' and 'shares' are required."})
        fcf = float(fcf)
        shares = float(shares)
        if shares <= 0:
            return json.dumps({"error": "'shares' must be positive."})
        g1 = float(kwargs.get("growth_rate_1_5", 0.05))
        # Sanity-check: if growth looks like a percentage (> 1), convert to decimal
        if g1 > 1:
            g1 = g1 / 100
        g2 = kwargs.get("growth_rate_6_10")
        if g2 is None:
            g2 = g1 / 2
        else:
            g2 = float(g2)
            if g2 > 1:
                g2 = g2 / 100
        discount = float(kwargs.get("discount_rate", 0.10))
        if discount > 1:
            discount = discount / 100
        multiple = float(kwargs.get("terminal_multiple", 12.0))
        price = kwargs.get("price")

        pv_cashflows = 0.0
        cf = fcf
        yearly = []

        for yr in range(1, 11):
            g = g1 if yr <= 5 else g2
            cf *= (1 + g)
            pv = cf / (1 + discount) ** yr
            pv_cashflows += pv
            yearly.append({"year": yr, "fcf": round(cf, 2), "pv": round(pv, 2)})

        # Terminal value using exit multiple method
        terminal_value_raw = cf * multiple
        pv_terminal = terminal_value_raw / (1 + discount) ** 10

        total_intrinsic = pv_cashflows + pv_terminal
        iv_per_share = total_intrinsic / shares

        result = {
            "intrinsic_value_per_share": round(iv_per_share, 2),
            "total_intrinsic_value": round(total_intrinsic, 2),
            "pv_of_cashflows": round(pv_cashflows, 2),
            "pv_of_terminal": round(pv_terminal, 2),
            "yearly_breakdown": yearly,
            "inputs": {
                "fcf": fcf,
                "shares": shares,
                "growth1": g1,
                "growth2": g2,
                "discount": discount,
                "multiple": multiple
            }
        }

        if price is not None:
            price = float(price)
            if iv_per_share <= 0:
                mos = -100.0
                verdict = "❌ Negative intrinsic value — FCF does not support valuation"
            else:
                mos = (iv_per_share - price) / iv_per_share * 100
                if mos >= 50:
                    verdict = f"✅ Buy zone — {mos:.1f}% below intrinsic value"
                elif mos > 0:
                    verdict = f"⚠️ Insufficient margin — only {mos:.1f}% discount (need ≥50%)"
                else:
                    verdict = f"❌ Overvalued — trading {abs(mos):.1f}% above intrinsic value"
            result["margin_of_safety"] = {
                "current_price": price,
                "margin_of_safety_pct": round(mos, 1),
                "meets_threshold": mos >= 50,
                "verdict": verdict
            }

        logger.debug(f"Calculated DCF IV: {round(iv_per_share, 2)}")
        return json.dumps(sanitize_json(result), indent=2)
