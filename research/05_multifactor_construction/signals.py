"""Same four reference signals, self-contained copy for this study."""
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


def zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional z-score each row so different signals are comparable
    before averaging. Without this, a loud signal (high raw variance)
    drowns out a quiet one in the blend."""
    mean = df.mean(axis=1)
    std = df.std(axis=1).replace(0, np.nan)
    return df.sub(mean, axis=0).div(std, axis=0)


def blend_signal_streams(signals: dict, names: list, zscale: bool = True):
    """Average a subset of signal DataFrames after z-scoring.

    `signals` maps name -> DataFrame. `names` is the subset to include.
    Returns a single DataFrame of blended scores.
    """
    parts = [zscore(signals[n]) if zscale else signals[n] for n in names]
    return sum(parts) / len(parts)


SIGNAL_REGISTRY = {
    "mom12":  signal_mom12,
    "mom1":   signal_mom1,
    "lowvol": signal_lowvol,
    "mr5":    signal_mr5,
}
