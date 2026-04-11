"""Same four signals + backtest-level strategy return stream builder.

The difference vs earlier studies: this study operates on a 4-wide
*strategy* return matrix (one column per signal), not on the 10-wide
*asset* return matrix. The portfolio optimizer allocates across
strategies, each of which internally runs its own quintile L/S book.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def signal_mom12(returns):
    return (1 + returns).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True).shift(1)


def signal_mom1(returns):
    return -returns.shift(1)


def signal_lowvol(returns):
    return (-returns.rolling(12).std()).shift(1)


def signal_mr5(returns):
    cum5 = (1 + returns).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    z = (cum5 - cum5.rolling(12).mean()) / cum5.rolling(12).std().replace(0, np.nan)
    return (-z).shift(1)


SIGNAL_REGISTRY = {
    "mom12":  signal_mom12,
    "mom1":   signal_mom1,
    "lowvol": signal_lowvol,
    "mr5":    signal_mr5,
}


def equal_weight(strategies: pd.DataFrame) -> pd.Series:
    """1/N across non-null columns every period. Baseline."""
    w = pd.DataFrame(1.0 / strategies.shape[1], index=strategies.index, columns=strategies.columns)
    return (strategies * w).sum(axis=1)


def inverse_vol(strategies: pd.DataFrame, lookback: int) -> pd.Series:
    """Inverse 24-month rolling-vol weights, rebalanced monthly."""
    vol = strategies.rolling(lookback).std()
    w = 1.0 / vol.replace(0, np.nan)
    w = w.div(w.sum(axis=1), axis=0).fillna(0)
    # Use lagged weights (weights based on info available at t, applied to t+1 return).
    return (w.shift(1) * strategies).sum(axis=1)


def minimum_variance(strategies: pd.DataFrame, lookback: int) -> pd.Series:
    """Global minimum-variance portfolio on a rolling covariance estimate.

    w = Σ^{-1} 1 / (1' Σ^{-1} 1). No shorting constraint — the
    underlying strategy streams can already be short, so unconstrained
    is closer to the "math-textbook" answer this study is stress-testing.
    """
    rows = []
    cols = list(strategies.columns)
    for t in range(lookback, len(strategies)):
        window = strategies.iloc[t - lookback:t].dropna(how="any")
        if len(window) < lookback * 0.8 or window.shape[1] < 2:
            rows.append(pd.Series([np.nan] * len(cols), index=cols))
            continue
        cov = window.cov().values
        try:
            inv = np.linalg.pinv(cov)
        except np.linalg.LinAlgError:
            rows.append(pd.Series([np.nan] * len(cols), index=cols))
            continue
        ones = np.ones(len(cols))
        w = inv @ ones / (ones @ inv @ ones)
        rows.append(pd.Series(w, index=cols))

    w_df = pd.DataFrame(rows, index=strategies.index[lookback:])
    w_df = w_df.reindex(strategies.index).fillna(0)
    return (w_df.shift(1) * strategies).sum(axis=1)


def max_sharpe(strategies: pd.DataFrame, lookback: int) -> pd.Series:
    """Unconstrained max-Sharpe (Markowitz tangency) on rolling window.

    w ∝ Σ^{-1} μ, then renormalized to sum to 1. Notoriously unstable
    with short histories — that's part of the point of this study.
    """
    rows = []
    cols = list(strategies.columns)
    for t in range(lookback, len(strategies)):
        window = strategies.iloc[t - lookback:t].dropna(how="any")
        if len(window) < lookback * 0.8 or window.shape[1] < 2:
            rows.append(pd.Series([np.nan] * len(cols), index=cols))
            continue
        mu = window.mean().values
        cov = window.cov().values
        try:
            inv = np.linalg.pinv(cov)
            w = inv @ mu
            if abs(w.sum()) < 1e-9:
                rows.append(pd.Series([np.nan] * len(cols), index=cols))
                continue
            w = w / w.sum()
        except np.linalg.LinAlgError:
            rows.append(pd.Series([np.nan] * len(cols), index=cols))
            continue
        rows.append(pd.Series(w, index=cols))

    w_df = pd.DataFrame(rows, index=strategies.index[lookback:])
    w_df = w_df.reindex(strategies.index).fillna(0)
    return (w_df.shift(1) * strategies).sum(axis=1)


METHOD_REGISTRY = {
    "equal_weight":     equal_weight,
    "inverse_vol":      inverse_vol,
    "minimum_variance": minimum_variance,
    "max_sharpe":       max_sharpe,
}
