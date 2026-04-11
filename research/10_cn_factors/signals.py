"""A-share factor-proxy construction.

Each factor is a simple difference between two style-index monthly return
series. This is the "signal source" for the study — read this file and
you know exactly what every factor is and isn't.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def build_proxy_factor(
    panel: pd.DataFrame,
    long_label: str,
    short_label: str,
) -> pd.Series:
    """Factor_t = long_t - short_t.

    Returned series is aligned on the intersection of both columns' valid
    dates — any month where either side is missing is dropped. We do not
    forward-fill; a missing index value is an honest data gap, not
    something to paper over.
    """
    if long_label not in panel.columns:
        raise KeyError(f"long leg '{long_label}' not in panel (have: {list(panel.columns)})")
    if short_label not in panel.columns:
        raise KeyError(f"short leg '{short_label}' not in panel (have: {list(panel.columns)})")
    long_rets = panel[long_label]
    short_rets = panel[short_label]
    aligned = pd.concat([long_rets, short_rets], axis=1).dropna()
    return (aligned.iloc[:, 0] - aligned.iloc[:, 1]).rename(f"{long_label}_minus_{short_label}")


def build_all_factors(
    panel: pd.DataFrame,
    factor_specs: Dict[str, List[str]],
) -> Dict[str, pd.Series]:
    """Apply build_proxy_factor across a dict of specs from config.yaml."""
    out = {}
    for name, (long_lbl, short_lbl) in factor_specs.items():
        try:
            out[name] = build_proxy_factor(panel, long_lbl, short_lbl)
        except KeyError as e:
            print(f"  [signals] skip {name}: {e}")
    return out


def us_vol_regime(
    us_mkt: pd.Series,
    window: int = 6,
) -> pd.DataFrame:
    """Classify each month as 'low' or 'high' U.S. vol.

    The regime cutoff is an *expanding median* of the rolling 6m annualised
    volatility — i.e. at each point the threshold uses only information
    available through that month, so this is an online classifier, not a
    lookahead bias.

    Returns a DataFrame with columns ['vol', 'median', 'regime'].
    """
    vol = us_mkt.rolling(window).std() * np.sqrt(12)
    median = vol.expanding(min_periods=window * 2).median()
    regime = pd.Series("unknown", index=vol.index)
    regime[vol < median] = "low"
    regime[vol >= median] = "high"
    return pd.DataFrame({"vol": vol, "median": median, "regime": regime})


def value_growth_cycle(
    hml: pd.Series,
    windows: List[Tuple[str, str, str]],
) -> list:
    """Summarize the Value-minus-Growth cycle over a list of windows.

    Each output entry reports cumulative return, Sharpe, and which side
    won. Cycles are long in A-shares (often 3+ years), which is why this
    factor gets its own section in the study.
    """
    out = []
    for start, end, label in windows:
        sub = hml[(hml.index >= start) & (hml.index <= end)]
        if len(sub) < 6 or sub.std() == 0:
            continue
        cum = float((1 + sub).prod() - 1)
        sharpe = float(sub.mean() / sub.std() * np.sqrt(12))
        out.append({
            "period": label,
            "cumulative_return": round(cum, 6),
            "sharpe": round(sharpe, 4),
            "winner": "Value" if cum > 0 else "Growth",
            "n_periods": int(len(sub)),
        })
    return out
