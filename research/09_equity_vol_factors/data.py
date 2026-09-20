"""Daily-returns panel loader for vol factors. yfinance only.

Lives here (not in _core) because this is the only study that needs
daily frequency — every other study works off the monthly panel.
Cached separately under data_cache/etf_daily_*.pkl.
"""
from __future__ import annotations

import os
import pickle
from typing import List, Optional

import pandas as pd

from research._core import frozen as _frozen

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data_cache"
)


def load_daily_panel(
    tickers: List[str],
    start: str,
    end: Optional[str] = None,
) -> pd.DataFrame:
    key = f"etf_daily_{'_'.join(sorted(tickers))[:80]}_{start}_{end or 'now'}"

    frozen_panel = _frozen.load(key)
    if frozen_panel is not None:
        return frozen_panel

    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{key}.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)

    import yfinance as yf
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    rets = close.pct_change().dropna(how="all")

    with open(path, "wb") as f:
        pickle.dump(rets, f)
    return rets
