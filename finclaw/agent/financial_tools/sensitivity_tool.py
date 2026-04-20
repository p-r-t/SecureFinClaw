"""Valuation Sensitivity Matrix Tool."""

import json
from typing import Any
from pydantic import ConfigDict
from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

class ValuationSensitivityTool(Tool):
    """Generates a sensitivity matrix for DCF valuation using Dhandho-style fixed axes."""

    name = "valuation_sensitivity"
    description = (
        "Generates a 3-D sensitivity matrix for a DCF valuation. "
        "Varies growth (3%, 5%, 8%), discount (10%, 12%, 15%), and exit multiple (10, 12, 15)."
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
            }
        },
        "required": ["fcf", "shares"]
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _calculate_single_dcf(self, fcf: float, g: float, d: float, m: float, shares: float) -> float:
        """Internal helper for two-stage DCF math."""
        # Stage 1: Years 1-5 (full growth), 6-10 (half growth)
        pv_cashflows = 0.0
        cf = fcf
        g1 = g
        g2 = g / 2
        for yr in range(1, 11):
            curr_g = g1 if yr <= 5 else g2
            cf *= (1 + curr_g)
            pv_cashflows += cf / (1 + d) ** yr
        
        terminal_value = cf * m
        pv_terminal = terminal_value / (1 + d) ** 10
        total_iv = pv_cashflows + pv_terminal
        return round(total_iv / shares, 2)

    async def execute(self, **kwargs: Any) -> str:
        fcf = float(kwargs.get("fcf", 0.0))
        shares = float(kwargs.get("shares", 1.0))

        # Dhandho fixed axes
        growth_rates = [0.03, 0.05, 0.08]
        discount_rates = [0.10, 0.12, 0.15]
        terminal_multiples = [10, 12, 15]

        matrix = {}
        all_ivs = []

        for g in growth_rates:
            g_key = f"{g:.0%}"
            matrix[g_key] = {}
            for d in discount_rates:
                d_key = f"{d:.0%}"
                matrix[g_key][d_key] = {}
                for m in terminal_multiples:
                    m_key = str(int(m))
                    val = self._calculate_single_dcf(fcf, g, d, m, shares)
                    matrix[g_key][d_key][m_key] = val
                    all_ivs.append(val)

        sorted_ivs = sorted(all_ivs)
        result = {
            "matrix": matrix,
            "growth_rates": [f"{g:.0%}" for g in growth_rates],
            "discount_rates": [f"{d:.0%}" for d in discount_rates],
            "terminal_multiples": [str(int(m)) for m in terminal_multiples],
            "summary": {
                "bear_case": round(min(all_ivs), 2),
                "base_case": round(sorted_ivs[len(sorted_ivs) // 2], 2),
                "bull_case": round(max(all_ivs), 2)
            }
        }

        # Generate a markdown table for the base multiple (12x)
        m_base = "12"
        md = f"### Sensitivity Matrix (at {m_base}x terminal multiple)\n\n"
        md += "| Discount \\ Growth | " + " | ".join([f"{g:.0%}" for g in growth_rates]) + " |\n"
        md += "| --- | " + "--- | " * len(growth_rates) + "\n"
        for d in discount_rates:
            d_key = f"{d:.0%}"
            md += f"| **{d_key}** | " + " | ".join([f"${matrix[f'{g:.0%}'][d_key][m_base]:.2f}" for g in growth_rates]) + " |\n"

        result["markdown_table"] = md
        return json.dumps(sanitize_json(result), indent=2)
