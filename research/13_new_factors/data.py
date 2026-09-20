"""FRED macro fetcher via pandas_datareader — public and free."""
from __future__ import annotations

import os
import pickle
from typing import List

import pandas as pd

from research._core import frozen as _frozen

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data_cache"
)


def fetch_fred_macros(series_ids: List[str], start: str, end: str) -> pd.DataFrame:
    """Pull daily FRED series, forward-fill to business days.

    Cached to data_cache/fred_<hash>.pkl.
    """
    key = f"fred_{'_'.join(sorted(series_ids))}_{start}_{end}"

    frozen_panel = _frozen.load(key)
    if frozen_panel is not None:
        return frozen_panel

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{key}.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)

    import pandas_datareader.data as pdr
    df = pdr.DataReader(series_ids, "fred", start=start, end=end)
    df = df.ffill()

    with open(path, "wb") as f:
        pickle.dump(df, f)
    return df
