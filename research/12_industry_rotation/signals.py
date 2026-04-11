"""Signal construction for the industry rotation study.

The whole study is less than 100 lines once you strip away the plumbing —
this file is the "signal source code" a reader can open and *see* the
strategy. Don't push logic back into the _core library.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def trailing_momentum(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Rolling-window momentum: product of (1 + r) over the last `lookback`
    months, minus 1. Shifted by one period so the signal at date t is only
    using information available *at* t, not peeking at t's own return.

    Output has NaNs for the first `lookback` rows.
    """
    cum = returns.rolling(lookback).apply(lambda x: np.prod(1 + x) - 1, raw=True)
    return cum.shift(1)


def topn_bottomn_long_short(
    mom_signal: pd.DataFrame,
    industry_returns: pd.DataFrame,
    top_n: int,
    bottom_n: int,
) -> Tuple[pd.Series, pd.DataFrame]:
    """Long equal-weight the top `top_n` industries by momentum, short the
    bottom `bottom_n`, rebalance monthly.

    Returns
    -------
    ls_returns : pd.Series   of monthly L/S returns (long minus short)
    legs       : pd.DataFrame with columns ['long_ret', 'short_ret'] for
                 diagnostic / plotting use.
    """
    rows = []
    for date in mom_signal.index:
        row = mom_signal.loc[date].dropna().sort_values()
        if len(row) < max(top_n, bottom_n) * 2:
            continue
        long_names = row.tail(top_n).index
        short_names = row.head(bottom_n).index
        long_ret = industry_returns.loc[date, long_names].mean()
        short_ret = industry_returns.loc[date, short_names].mean()
        rows.append({
            "date": date,
            "long_ret": float(long_ret),
            "short_ret": float(short_ret),
            "ls": float(long_ret - short_ret),
        })

    df = pd.DataFrame(rows).set_index("date")
    if df.empty:
        return pd.Series(dtype=float), df
    return df["ls"].rename("ls_returns"), df[["long_ret", "short_ret"]]


def decile_hi_lo_spread(mom_deciles: pd.DataFrame) -> pd.Series:
    """Ken French ships the 10 prior-return deciles directly. The canonical
    momentum factor is just `Hi PRIOR - Lo PRIOR`, no construction needed.
    We surface it as a reference point to compare against the coarser
    industry-level long/short above.
    """
    if "Hi PRIOR" not in mom_deciles.columns or "Lo PRIOR" not in mom_deciles.columns:
        raise KeyError(
            "decile_hi_lo_spread expects columns 'Hi PRIOR' and 'Lo PRIOR' "
            "(these are the standard Ken French names — something is wrong "
            "with the fetched dataset)."
        )
    return (mom_deciles["Hi PRIOR"] - mom_deciles["Lo PRIOR"]).rename("decile_spread")


def premium_hi_minus_lo(portfolios: pd.DataFrame) -> pd.Series:
    """Generic Hi-minus-Lo over a Ken French N-portfolio sort.

    Used for operating-profitability (OP) and investment (INV) premia:
    last column is the highest bucket, first column the lowest.
    """
    if portfolios.shape[1] < 2:
        raise ValueError("premium_hi_minus_lo needs at least 2 portfolios")
    return (portfolios.iloc[:, -1] - portfolios.iloc[:, 0]).rename("hi_minus_lo")
