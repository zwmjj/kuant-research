"""Unified returns-panel loader for every study.

Four sources, probed in order (caller can pin one via `source=...`):

    0. frozen   — versioned CSV in research/_data_frozen/<name>.csv, written
                  once by tools/freeze_data.py and committed. This is what
                  makes a fresh clone reproduce with no network at all, and
                  what pins the result against upstream data changing.
    1. cache    — pre-built pickle in kuant-research/data_cache/<name>.pkl
                  (a local working cache; not versioned)
    2. yfinance — download on demand given a ticker list
                  (<=100 tickers, monthly resample)
    3. csv      — user-supplied CSV for studies with proprietary data
                  (expected shape: Date index, one column per asset, monthly)

All three return the same shape: a `returns` DataFrame whose index is a
`pd.DatetimeIndex` at month-end and whose columns are asset IDs.

This loader is intentionally small. If a study needs something exotic
(Compustat fundamentals, CRSP delisting flags), it ships its own fetcher
in that study's folder — don't push study-specific logic into core.
"""
from __future__ import annotations

import os
import pickle
from typing import List, Optional

import numpy as np
import pandas as pd

from research._core import frozen as _frozen

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data_cache"
)


def load_returns_panel(
    tickers: Optional[List[str]] = None,
    start: str = "2010-01-01",
    end: Optional[str] = None,
    source: str = "auto",
    cache_name: Optional[str] = None,
    csv_path: Optional[str] = None,
) -> pd.DataFrame:
    """Return a monthly-returns panel, sourced from the first available backend.

    Parameters
    ----------
    tickers : list of str, optional
        Required for source='yfinance'. Ignored by cache/csv which already
        carry their own column set.
    start, end : str
        Inclusive date bounds. `end=None` means "today".
    source : {'auto', 'frozen', 'cache', 'yfinance', 'csv'}
        'auto' tries frozen -> cache -> yfinance -> csv in order. Pin
        'frozen' to guarantee a run touches no network and uses exactly the
        committed data.
    cache_name : str
        Filename (without .pkl) in data_cache/. Defaults to joined ticker hash.
    csv_path : str
        Absolute path to a CSV file when source='csv'.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    if source in ("auto", "frozen") and cache_name:
        panel = _frozen.load(cache_name)
        if panel is not None:
            return _slice(panel, start, end)
        if source == "frozen":
            raise FileNotFoundError(
                f"No frozen panel named '{cache_name}'. Run tools/freeze_data.py "
                "on a machine with network access to create it."
            )

    if source in ("auto", "cache") and cache_name:
        path = os.path.join(CACHE_DIR, f"{cache_name}.pkl")
        if os.path.exists(path):
            with open(path, "rb") as f:
                panel = pickle.load(f)
            return _slice(panel, start, end)
        if source == "cache":
            raise FileNotFoundError(f"Cache miss: {path}")

    if source in ("auto", "yfinance") and tickers:
        panel = _fetch_yfinance(tickers, start, end)
        if cache_name:
            with open(os.path.join(CACHE_DIR, f"{cache_name}.pkl"), "wb") as f:
                pickle.dump(panel, f)
        return _slice(panel, start, end)

    if source in ("auto", "csv") and csv_path:
        panel = _read_csv(csv_path)
        return _slice(panel, start, end)

    raise ValueError(
        "load_returns_panel: no source worked. "
        "Pass `tickers=[...]` for yfinance, `cache_name=...` for a prebuilt "
        "pickle, or `csv_path=...` for a CSV file."
    )


def _fetch_yfinance(tickers, start, end):
    import yfinance as yf
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    close = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    # Resample to month-end and take the last observation, then pct_change.
    monthly = close.resample("ME").last()
    rets = monthly.pct_change().dropna(how="all")
    return rets


def _read_csv(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df = df.sort_index()
    return df


def _slice(panel: pd.DataFrame, start: str, end: Optional[str]) -> pd.DataFrame:
    if start:
        panel = panel[panel.index >= start]
    if end:
        panel = panel[panel.index <= end]
    return panel
