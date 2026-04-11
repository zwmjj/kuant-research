"""Quintile long-short backtest engine.

Contract:
    signal  : pd.DataFrame of signal values (index=rebalance dates,
              columns=asset IDs). Higher = more attractive (long).
              Assets with NaN at time t are ignored that period.
    returns : pd.DataFrame of *forward* returns (index aligned to signal,
              columns=asset IDs). returns.loc[t, a] is the return earned by
              an asset held from t to t+1.

The engine:
    1. Ranks assets cross-sectionally at each t.
    2. Goes equal-weight long in the top `quantile` fraction, equal-weight
       short in the bottom `quantile`. Gross exposure is 2x.
    3. Applies turnover_penalty via signal shrinkage (Exponential blend).
    4. Charges a cost per `CostConfig` on the realized weight change.

This is the same quintile-spread methodology used across the Kuant research
book — intentionally simple so every study's result is reproducible from
returns data alone.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd

from research._core.costs import CostConfig, apply_turnover_cost


def _shrink_signal(signal: pd.DataFrame, penalty: float) -> pd.DataFrame:
    """Blend new signal with the prior period's signal.

    penalty=0 -> no shrinkage (use raw signal every rebalance, max turnover)
    penalty=1 -> freeze signal to its first valid value (zero rebalances after t0)
    """
    if penalty <= 0:
        return signal
    if penalty >= 1.0:
        # Fully frozen: hold the first non-null row forward. Pandas' ewm
        # requires alpha > 0, so we handle this edge case explicitly rather
        # than clamping which would silently change behavior at the boundary.
        first_row = signal.bfill().iloc[0]
        return pd.DataFrame(
            [first_row.values] * len(signal),
            index=signal.index, columns=signal.columns,
        )
    alpha = 1.0 - penalty  # weight on new signal, in (0, 1)
    return signal.ewm(alpha=alpha, adjust=False).mean()


def _quintile_weights(signal_row: pd.Series, quantile: float) -> pd.Series:
    """Equal-weight long top quintile, short bottom quintile."""
    valid = signal_row.dropna()
    if len(valid) < 5:
        return pd.Series(0.0, index=signal_row.index)
    n_side = max(int(round(len(valid) * quantile)), 1)
    ranked = valid.sort_values()
    short = ranked.head(n_side).index
    long_ = ranked.tail(n_side).index
    w = pd.Series(0.0, index=signal_row.index)
    w.loc[long_] = 1.0 / n_side
    w.loc[short] = -1.0 / n_side
    return w


def long_short_quintile_backtest(
    signal: pd.DataFrame,
    returns: pd.DataFrame,
    quantile: float = 0.2,
    cost_config: Optional[CostConfig] = None,
) -> Tuple[pd.Series, pd.DataFrame]:
    """Run the backtest, return (net_returns, weights).

    Both outputs are indexed by rebalance date. `net_returns.iloc[t]` is the
    realized period-return of the book between dates t and t+1, net of cost.
    """
    cfg = cost_config or CostConfig()

    # Align signal and returns on intersection of dates+assets.
    common_dates = signal.index.intersection(returns.index)
    common_cols = signal.columns.intersection(returns.columns)
    sig = signal.loc[common_dates, common_cols]
    rets = returns.loc[common_dates, common_cols]

    sig_shrunk = _shrink_signal(sig, cfg.turnover_penalty)

    weights = pd.DataFrame(0.0, index=sig_shrunk.index, columns=sig_shrunk.columns)
    for t in sig_shrunk.index:
        weights.loc[t] = _quintile_weights(sig_shrunk.loc[t], quantile)

    # Gross return = sum(w_t * r_t) — r_t is the *forward* return, so we
    # take w_t from the previous rebalance and apply it to this period.
    gross = (weights.shift(1) * rets).sum(axis=1)
    gross.iloc[0] = 0.0  # first period has no prior weights

    net = apply_turnover_cost(gross, weights, cfg)
    return net, weights
