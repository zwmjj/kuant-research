"""Signal + regime scaling for the regime-timing study."""
from __future__ import annotations

import numpy as np
import pandas as pd


def signal_mom12(returns):
    return (1 + returns).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True).shift(1)


def signal_mr5(returns):
    cum5 = (1 + returns).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    z = (cum5 - cum5.rolling(12).mean()) / cum5.rolling(12).std().replace(0, np.nan)
    return (-z).shift(1)


SIGNAL_REGISTRY = {
    "mom12": signal_mom12,
    "mr5":   signal_mr5,
}


def vix_regime(vix: pd.Series, lookback_months: int = 12) -> pd.Series:
    """Classify each month as 'low' or 'high' VIX.

    Threshold is the expanding median of the rolling N-month VIX
    level. Uses only past information at each date, so this is an
    online (no lookahead) classifier.
    """
    vix_m = vix.resample("ME").last()
    # Rolling mean acts as a smoother of the raw VIX level.
    smoothed = vix_m.rolling(lookback_months).mean()
    thresh = smoothed.expanding(lookback_months).median()
    regime = pd.Series("unknown", index=vix_m.index)
    regime[smoothed >= thresh] = "high"
    regime[smoothed < thresh] = "low"
    return regime


def apply_rule(raw_returns: pd.Series, regime: pd.Series, rule: str) -> pd.Series:
    """Apply a scaling rule to a strategy return stream.

    The rule names match `config.yaml`'s `rules` list.
    """
    aligned = regime.reindex(raw_returns.index, method="ffill")
    scale = pd.Series(0.0, index=raw_returns.index)
    if rule == "full":
        scale[:] = 1.0
    elif rule == "risk_off_only":
        scale[aligned == "high"] = 1.0
    elif rule == "risk_on_only":
        scale[aligned == "low"] = 1.0
    elif rule == "scaled":
        scale[aligned == "low"] = 1.5
        scale[aligned == "high"] = 0.5
    elif rule == "anti_scaled":
        scale[aligned == "low"] = 0.5
        scale[aligned == "high"] = 1.5
    else:
        raise ValueError(f"unknown rule '{rule}'")
    return raw_returns * scale
