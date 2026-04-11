"""Same four price-based signals as 01_signal_decay_vs_cost.

Duplicated (rather than imported from ../01_signal_decay_vs_cost) so each
study folder stays self-contained and readers can see the signal source
without jumping between directories.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def signal_mom12(returns: pd.DataFrame) -> pd.DataFrame:
    """12-month trailing momentum, shifted to avoid lookahead."""
    cum = (1 + returns).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True)
    return cum.shift(1)


def signal_mom1(returns: pd.DataFrame) -> pd.DataFrame:
    """1-month short-term reversal: -return_{t-1}."""
    return -returns.shift(1)


def signal_lowvol(returns: pd.DataFrame) -> pd.DataFrame:
    """Negative 12-month rolling std — low-vol preferred."""
    return (-returns.rolling(12).std()).shift(1)


def signal_mr5(returns: pd.DataFrame) -> pd.DataFrame:
    """5-month return z-scored against a 12-month rolling moment, negated."""
    cum5 = (1 + returns).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    z = (cum5 - cum5.rolling(12).mean()) / cum5.rolling(12).std().replace(0, np.nan)
    return (-z).shift(1)


SIGNAL_REGISTRY = {
    "mom12":  signal_mom12,
    "mom1":   signal_mom1,
    "lowvol": signal_lowvol,
    "mr5":    signal_mr5,
}
