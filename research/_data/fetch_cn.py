"""A-share index fetchers via akshare (public, free, no credentials).

Returns the same contract as the Ken French fetchers: monthly returns in
decimal, DatetimeIndex at month-end, one column per index.
"""
from __future__ import annotations

import os
import pickle
from typing import Dict, Optional

import pandas as pd

from research._core import frozen as _frozen

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data_cache"
)

# Style indices used by the cn_factors study. akshare naming convention:
#   sh... = Shanghai, sz... = Shenzhen. These are the canonical CSI/SSE
#   style indices the study needs; don't add exotic ones without updating
#   the study's config.yaml in lockstep.
DEFAULT_INDICES: Dict[str, str] = {
    "CSI300":   "sh000300",  # large-cap benchmark
    "CSI500":   "sh000905",  # mid-cap benchmark
    "CSI1000":  "sh000852",  # small-cap benchmark
    "GEM":      "sz399006",  # ChiNext growth board
    "Value":    "sh000029",  # Shanghai 180 Value
    "Growth":   "sh000030",  # Shanghai 180 Growth
    "Dividend": "sh000922",  # Dividend Index
    "LowVol":   "sh000803",  # Low Volatility Index
}


def fetch_cn_indices(
    indices: Optional[Dict[str, str]] = None,
    start: str = "2010-01-01",
) -> pd.DataFrame:
    """Download monthly returns for a set of A-share indices.

    Parameters
    ----------
    indices : dict {label: akshare_symbol}, optional
        Defaults to DEFAULT_INDICES (the 8 style indices used by the
        cn_factors study). Pass your own dict to add coverage.
    start : str
        Earliest date to keep after resampling.

    Returns
    -------
    pd.DataFrame — month-end DatetimeIndex, one column per label.
    """
    idx_map = indices or DEFAULT_INDICES
    cache_key = f"cn_{'_'.join(sorted(idx_map.keys()))}_{start}"

    # Frozen copy first: akshare scrapes an unofficial endpoint, so a
    # published result must not depend on it still answering the same way.
    frozen_panel = _frozen.load(cache_key)
    if frozen_panel is not None:
        return frozen_panel

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{cache_key}.pkl")

    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)

    import time

    import akshare as ak

    series, failed = {}, {}
    for label, sym in idx_map.items():
        # The upstream endpoint resets the connection under rapid sequential
        # requests. Retry with backoff, and space the calls out: without this
        # a run silently returns a panel with fewer indices than it asked for,
        # which changes the universe a study is computed on without changing
        # anything the study can see. That is the worst kind of data bug —
        # every downstream number moves and nothing reports an error.
        raw, last_err = None, None
        for attempt in range(4):
            try:
                raw = ak.stock_zh_index_daily(symbol=sym)
                break
            except Exception as e:  # noqa: BLE001 - upstream raises bare errors
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        if raw is None:
            failed[label] = f"{sym}: {type(last_err).__name__}: {last_err}"
            continue

        raw["date"] = pd.to_datetime(raw["date"])
        raw = raw.set_index("date").sort_index()
        monthly = raw["close"].resample("ME").last()
        ret = monthly.pct_change().dropna()
        ret = ret[ret.index >= start]
        series[label] = ret
        time.sleep(1.0)

    if failed:
        # Fail loudly. A partial panel is not a smaller version of the same
        # study, it is a different study.
        detail = "\n".join(f"    {k} -> {v}" for k, v in failed.items())
        raise RuntimeError(
            f"fetch_cn_indices: {len(failed)} of {len(idx_map)} indices could not "
            f"be fetched after retries, so the panel would be missing columns the "
            f"study expects:\n{detail}\n"
            f"  Re-run when the upstream endpoint settles. Do not freeze a partial panel."
        )

    df = pd.DataFrame(series)
    with open(path, "wb") as f:
        pickle.dump(df, f)
    return df
