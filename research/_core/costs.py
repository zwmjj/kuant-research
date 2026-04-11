"""Transaction cost model for the long-short engine.

Deliberately simple: a proportional cost (bps of notional) plus a square-root
market-impact term, both driven by a single `penalty` knob the studies sweep.
The goal isn't production accuracy — it's reproducibility of the *shape* of
the cost/Sharpe trade-off that every study in this folder plots.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CostConfig:
    """Bundle the four knobs that drive cost.

    commission_bps : flat per-trade fee (buy & sell), in basis points
    spread_bps     : half-spread paid on each fill, in basis points
    impact_coeff   : coefficient on sqrt(turnover) impact term, in decimal
                     (e.g. 0.3 means 30% of sqrt(turnover) gets charged)
    turnover_penalty : direct shrink applied to signal changes, unitless.
                       Higher -> lazier rebalancing -> lower realized turnover.
    """
    commission_bps: float = 1.0
    spread_bps: float = 5.0
    impact_coeff: float = 0.3
    turnover_penalty: float = 0.25

    @property
    def flat_bps(self) -> float:
        """Total flat cost per unit of traded notional, in decimal."""
        return (self.commission_bps + self.spread_bps) / 10000.0


def apply_turnover_cost(
    raw_returns: pd.Series,
    weights: pd.DataFrame,
    cfg: CostConfig,
) -> pd.Series:
    """Charge cost on every rebalance.

    turnover_t = 0.5 * sum_i |w_{i,t} - w_{i,t-1}|
    cost_t     = turnover_t * (flat_bps + impact_coeff * sqrt(turnover_t))

    Returns a new Series with the same index as `raw_returns`.
    """
    turnover = 0.5 * weights.diff().abs().sum(axis=1).fillna(0)
    impact = cfg.impact_coeff * np.sqrt(turnover.clip(lower=0))
    cost = turnover * (cfg.flat_bps + impact / 10000.0)
    # Align cost to return index — anything missing = no rebalance that period.
    cost = cost.reindex(raw_returns.index).fillna(0)
    return raw_returns - cost
