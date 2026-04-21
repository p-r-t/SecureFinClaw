"""
Quantitative Valuation Reference Scripts
Pure Python Implementation without external dependencies.
"""

from typing import List, Optional

class DCF:
    def __init__(
        self,
        fcf_current: float,
        growth_rates: List[float],
        wacc: float,
        terminal_growth: Optional[float] = None,
        exit_multiple: Optional[float] = None,
    ):
        if terminal_growth is None and exit_multiple is None:
            raise ValueError("Provide either terminal_growth or exit_multiple.")
        if terminal_growth is not None and terminal_growth >= wacc:
            raise ValueError("terminal_growth must be less than wacc.")

        self.fcf_current = fcf_current
        self.growth_rates = growth_rates
        self.wacc = wacc
        self.terminal_growth = terminal_growth
        self.exit_multiple = exit_multiple

    def projected_fcfs(self) -> List[float]:
        fcfs = []
        fcf = self.fcf_current
        for g in self.growth_rates:
            fcf = fcf * (1.0 + g)
            fcfs.append(fcf)
        return fcfs

    def pv_explicit_fcfs(self) -> float:
        fcfs = self.projected_fcfs()
        pv = 0.0
        for i, fcf in enumerate(fcfs, start=1):
            pv += fcf / ((1.0 + self.wacc) ** i)
        return pv

    def terminal_value(self) -> float:
        fcfs = self.projected_fcfs()
        final_fcf = fcfs[-1]
        if self.terminal_growth is not None:
            return final_fcf * (1.0 + self.terminal_growth) / (self.wacc - self.terminal_growth)
        else:
            return final_fcf * self.exit_multiple

    def pv_terminal_value(self) -> float:
        n = len(self.growth_rates)
        tv = self.terminal_value()
        return tv / ((1.0 + self.wacc) ** n)

    def enterprise_value(self) -> float:
        return self.pv_explicit_fcfs() + self.pv_terminal_value()

    def equity_value(self, net_debt: float = 0.0) -> float:
        return self.enterprise_value() - net_debt

    def sensitivity_table(
        self, wacc_range: List[float], growth_range: List[float]
    ) -> List[List[float]]:
        if self.terminal_growth is None:
            raise ValueError("Sensitivity table requires Gordon Growth method.")

        results = []
        original_wacc = self.wacc
        original_tg = self.terminal_growth

        for w in wacc_range:
            row = []
            for g in growth_range:
                if g >= w:
                    row.append(float('nan'))
                    continue
                self.wacc = w
                self.terminal_growth = g
                row.append(self.enterprise_value())
            results.append(row)

        self.wacc = original_wacc
        self.terminal_growth = original_tg
        return results

class WACC:
    @staticmethod
    def cost_of_equity_capm(risk_free_rate: float, beta: float, equity_risk_premium: float) -> float:
        return risk_free_rate + beta * equity_risk_premium

    @staticmethod
    def compute(equity_weight: float, debt_weight: float, cost_of_equity: float, cost_of_debt: float, tax_rate: float) -> float:
        return (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1.0 - tax_rate))

if __name__ == "__main__":
    dcf = DCF(100.0, [0.15]*5, 0.10, terminal_growth=0.03)
    print(f"Enterprise Value: {dcf.enterprise_value()}")
