"""Vol-based factor signals built from daily returns.

Each function takes a **daily** returns DataFrame and returns a
**monthly** signal DataFrame indexed at month-end — the rolling
estimate is computed daily for stability, then downsampled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DAILY_TO_MONTHLY_LOOKBACK = 252  # 12 trading months


def _monthly(daily_signal: pd.DataFrame) -> pd.DataFrame:
    """Take the last daily value in each month."""
    return daily_signal.resample("ME").last()


def signal_rvol_12m(daily: pd.DataFrame) -> pd.DataFrame:
    """Realized 12-month daily-return vol, negated (low-vol preferred)."""
    vol = daily.rolling(DAILY_TO_MONTHLY_LOOKBACK).std() * np.sqrt(252)
    return _monthly(-vol).shift(1)


def signal_downvol_12m(daily: pd.DataFrame) -> pd.DataFrame:
    """Downside semi-deviation: std of returns after positives are
    clipped to zero. Negated so low downside-vol gets a high signal.

    We use `.clip(upper=0)` instead of `.where(daily<0)` because the
    where-NaN path interacts badly with rolling(min_periods) — every
    window ends up with fewer than 252 non-NaN values and the rolling
    std returns NaN across the board. Clipping positives to 0 keeps
    252 observations per window and computes semi-deviation
    correctly (Sortino-style).
    """
    neg_only = daily.clip(upper=0)
    downvol = neg_only.rolling(DAILY_TO_MONTHLY_LOOKBACK).std() * np.sqrt(252)
    return _monthly(-downvol).shift(1)


def signal_volofvol(daily: pd.DataFrame) -> pd.DataFrame:
    """Vol of vol: rolling std of a 21-day rolling vol. Low vol-of-vol
    is usually considered preferable (more stable underlying volatility
    regime), so we negate it."""
    rolling21 = daily.rolling(21).std()
    vov = rolling21.rolling(DAILY_TO_MONTHLY_LOOKBACK).std()
    return _monthly(-vov).shift(1)


def signal_beta_spy(daily: pd.DataFrame) -> pd.DataFrame:
    """Rolling 12-month market beta vs SPY. Negate so low-beta ETFs
    rank higher (betting-against-beta, Frazzini-Pedersen 2014)."""
    if "SPY" not in daily.columns:
        raise KeyError("beta_spy needs SPY in the universe")
    mkt = daily["SPY"]
    # Rolling covariance between each column and the market, divided
    # by the market's rolling variance.
    cov = daily.rolling(DAILY_TO_MONTHLY_LOOKBACK).cov(mkt)
    var = mkt.rolling(DAILY_TO_MONTHLY_LOOKBACK).var()
    beta = cov.div(var, axis=0)
    return _monthly(-beta).shift(1)


def signal_skew(daily: pd.DataFrame) -> pd.DataFrame:
    """12-month skewness — positive skew preferred (lottery-like upside
    without downside tail). This is the opposite of the classic
    'lottery premium' (Bali et al. 2011), so results here can go either
    way depending on the universe."""
    skew = daily.rolling(DAILY_TO_MONTHLY_LOOKBACK).skew()
    return _monthly(skew).shift(1)


SIGNAL_REGISTRY = {
    "rvol_12m":    signal_rvol_12m,
    "downvol_12m": signal_downvol_12m,
    "volofvol":    signal_volofvol,
    "beta_spy":    signal_beta_spy,
    "skew":        signal_skew,
}
