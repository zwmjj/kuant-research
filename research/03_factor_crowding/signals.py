"""Same four reference signals. Re-exported so each study is self-contained."""
from __future__ import annotations

import numpy as np
import pandas as pd


def signal_mom12(returns: pd.DataFrame) -> pd.DataFrame:
    cum = (1 + returns).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True)
    return cum.shift(1)


def signal_mom1(returns: pd.DataFrame) -> pd.DataFrame:
    return -returns.shift(1)


def signal_lowvol(returns: pd.DataFrame) -> pd.DataFrame:
    return (-returns.rolling(12).std()).shift(1)


def signal_mr5(returns: pd.DataFrame) -> pd.DataFrame:
    cum5 = (1 + returns).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    z = (cum5 - cum5.rolling(12).mean()) / cum5.rolling(12).std().replace(0, np.nan)
    return (-z).shift(1)


SIGNAL_REGISTRY = {
    "mom12":  signal_mom12,
    "mom1":   signal_mom1,
    "lowvol": signal_lowvol,
    "mr5":    signal_mr5,
}
