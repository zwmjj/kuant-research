"""Four price-based signals used by the signal-decay study.

All take a monthly-returns DataFrame (columns = assets) and return a
signal DataFrame of the same shape. Higher signal = longer leg.

Intentionally no fundamentals / no macro — this study is about the
*shape* of the signal-cost trade-off, which is a property of signal
persistence, and price-based signals are enough to show every shape
a fundamental factor would produce.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def signal_mom12(returns: pd.DataFrame) -> pd.DataFrame:
    """12-month trailing momentum, shifted to avoid lookahead.

    `signal_t` = cumulative return over months [t-12, t-1].
    """
    cum = (1 + returns).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True)
    return cum.shift(1)


def signal_mom1(returns: pd.DataFrame) -> pd.DataFrame:
    """1-month short-term reversal.

    `signal_t` = -return_{t-1}. High past-month return → low signal
    (because we expect reversal).
    """
    return -returns.shift(1)


def signal_lowvol(returns: pd.DataFrame) -> pd.DataFrame:
    """Low-volatility: negative 12-month rolling std.

    `signal_t` = -stdev(returns_{t-12..t-1}). Lower historical vol →
    higher signal → preferred in the long leg.
    """
    vol = returns.rolling(12).std()
    return (-vol).shift(1)


def signal_mr5(returns: pd.DataFrame) -> pd.DataFrame:
    """5-month mean reversion.

    Z-score the 5-month cumulative return against a 12-month rolling
    mean/std of 5m returns, then negate so recent outperformers get
    a *lower* signal.
    """
    cum5 = (1 + returns).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    mean5 = cum5.rolling(12).mean()
    std5 = cum5.rolling(12).std()
    z = (cum5 - mean5) / std5.replace(0, np.nan)
    return (-z).shift(1)


# Registry so run.py can look up by string name.
SIGNAL_REGISTRY = {
    "mom12":  signal_mom12,
    "mom1":   signal_mom1,
    "lowvol": signal_lowvol,
    "mr5":    signal_mr5,
}


def build_signal(name: str, returns: pd.DataFrame) -> pd.DataFrame:
    if name not in SIGNAL_REGISTRY:
        raise KeyError(f"unknown signal '{name}'. known: {list(SIGNAL_REGISTRY)}")
    return SIGNAL_REGISTRY[name](returns)


def signal_autocorrelation(signal: pd.DataFrame, max_lag: int = 12) -> list:
    """Cross-sectional mean signal → autocorrelation at lags 1..max_lag.

    A 'half-life' proxy: the first lag at which autocorrelation drops
    below 0.5 tells you roughly how many months the signal persists
    before it's decorrelated from its own past.
    """
    avg = signal.mean(axis=1).dropna()
    acf = []
    for lag in range(1, max_lag + 1):
        ac = avg.autocorr(lag=lag)
        acf.append(round(float(ac if ac == ac else 0.0), 4))  # NaN → 0
    return acf
