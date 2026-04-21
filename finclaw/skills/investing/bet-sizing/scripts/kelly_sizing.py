"""
Bet Sizing Toolkit
Pure Python Implementation without external dependencies.
"""

from typing import List, Optional

class KellyCriterion:
    def __init__(self, expected_excess_return: float, volatility: float):
        self.expected_excess_return = expected_excess_return
        self.volatility = volatility

    @staticmethod
    def discrete_kelly(win_prob: float, payoff_odds: float) -> float:
        q = 1.0 - win_prob
        if payoff_odds <= 0:
            return 0.0
        kelly = (payoff_odds * win_prob - q) / payoff_odds
        return max(kelly, 0.0)

    def continuous_kelly(self) -> float:
        if self.volatility == 0:
            return 0.0
        return self.expected_excess_return / (self.volatility ** 2)

    def fractional_kelly(self, fraction: float = 0.5) -> float:
        return fraction * self.continuous_kelly()

class PositionSizer:
    @staticmethod
    def volatility_target_size(target_risk: float, asset_volatility: float) -> float:
        if asset_volatility == 0:
            return 0.0
        return target_risk / asset_volatility

    @staticmethod
    def max_drawdown_size(max_acceptable_drawdown: float, asset_volatility: float, drawdown_multiplier: float = 2.0) -> float:
        if asset_volatility == 0:
            return 0.0
        expected_max_dd = drawdown_multiplier * asset_volatility
        if expected_max_dd == 0:
            return 0.0
        return max_acceptable_drawdown / expected_max_dd

    @staticmethod
    def conviction_weighted_sizes(edge_scores: List[float], certainty_scores: List[float], max_position: float = 0.10) -> List[float]:
        raw_scores = [e * c for e, c in zip(edge_scores, certainty_scores)]
        max_score = max(raw_scores) if raw_scores else 0
        if max_score == 0:
            return [0.0 for _ in raw_scores]
        return [(score / max_score) * max_position for score in raw_scores]

if __name__ == "__main__":
    kelly = KellyCriterion(0.08, 0.20)
    print(f"Full Kelly: {kelly.continuous_kelly()}")
