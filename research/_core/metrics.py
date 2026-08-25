"""Return-stream metrics shared across all studies.

Input contract for every function:
    rets : pd.Series of *periodic* returns (monthly or daily), DatetimeIndex.
    periods_per_year : int (12 for monthly, 252 for daily).

Nothing in this module annualizes differently depending on caller frequency —
the caller tells us the scale.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


def compute_metrics(
    rets: pd.Series,
    periods_per_year: int = 12,
    rf: Optional[pd.Series] = None,
) -> dict:
    """Full summary stats for a single return stream.

    Returns a plain dict so every study's `expected_output.json` can be
    diffed without dragging pickles around.
    """
    rets = rets.dropna()
    if len(rets) < 2 or rets.std() == 0:
        return {
            "n_periods": int(len(rets)),
            "total_return": 0.0, "cagr": 0.0, "sharpe": 0.0,
            "sortino": 0.0, "max_drawdown": 0.0, "vol": 0.0,
            "win_rate": 0.0,
        }

    excess = rets if rf is None else rets - rf.reindex(rets.index).fillna(0)
    years = len(rets) / periods_per_year

    total_ret = float((1 + rets).prod() - 1)
    cagr = float((1 + total_ret) ** (1 / max(years, 1e-6)) - 1)
    vol = float(rets.std() * np.sqrt(periods_per_year))
    sharpe = float(excess.mean() / excess.std() * np.sqrt(periods_per_year))

    # Sortino uses target semi-deviation (Sortino & Price 1994): the
    # root-mean-square shortfall below the target — here 0 — averaged over
    # EVERY period, not just the losing ones:
    #
    #     downside = sqrt( mean_t[ min(r_t - target, 0)^2 ] )
    #
    # The common shortcut, `rets[rets < 0].std()`, differs on two counts: it
    # centres on the losers' own mean instead of the target, and it averages
    # over the losing periods only. Neither error has a fixed sign, so the
    # shortcut is not a conservative approximation — it is simply a different
    # statistic, and which way it lands depends on how frequent and how
    # dispersed the losses are.
    shortfall = np.minimum(rets.values, 0.0)
    downside = float(np.sqrt((shortfall ** 2).mean()) * np.sqrt(periods_per_year))
    sortino = float(excess.mean() * periods_per_year / downside) if downside > 0 else 0.0

    pv = (1 + rets).cumprod()
    dd = (pv - pv.cummax()) / pv.cummax()
    mdd = float(dd.min())

    return {
        "n_periods": int(len(rets)),
        "total_return": round(total_ret, 6),
        "cagr": round(cagr, 6),
        "sharpe": round(sharpe, 4),
        "sortino": round(sortino, 4),
        "max_drawdown": round(mdd, 6),
        "vol": round(vol, 6),
        "win_rate": round(float((rets > 0).mean()), 4),
    }


def split_is_oos(
    rets: pd.Series,
    split_date: str = "2020-12-31",
    periods_per_year: int = 12,
) -> dict:
    """Classic IS/OOS Sharpe decomposition around a fixed pivot date.

    The default 2020-12-31 pivot matches what the Kuant research book uses
    across every study — keep it in sync so cross-study numbers line up.
    """
    is_r = rets[rets.index <= split_date]
    oos_r = rets[rets.index > split_date]
    return {
        "split_date": split_date,
        "is":  compute_metrics(is_r,  periods_per_year=periods_per_year),
        "oos": compute_metrics(oos_r, periods_per_year=periods_per_year),
    }


def rolling_windows(
    rets: pd.Series,
    windows: List[Tuple[str, str, str]],
    periods_per_year: int = 12,
) -> list:
    """Compute Sharpe across a list of (start, end, label) windows.

    Skips any window with fewer than `periods_per_year // 2` observations so
    early-data or half-filled periods don't poison the output with
    undefined Sharpes.
    """
    out = []
    min_obs = max(periods_per_year // 2, 3)
    for start, end, label in windows:
        sub = rets[(rets.index >= start) & (rets.index <= end)]
        if len(sub) < min_obs or sub.std() == 0:
            continue
        out.append({
            "period": label,
            "sharpe": round(float(sub.mean() / sub.std() * np.sqrt(periods_per_year)), 4),
            "cum_return": round(float((1 + sub).prod() - 1), 6),
            "n_periods": int(len(sub)),
        })
    return out
