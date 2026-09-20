"""Kenneth French data library fetchers.

All functions return monthly `pd.DataFrame`s with a `DatetimeIndex` at
month-end and numeric returns in decimal (0.01 = 1%). The raw Ken French
files are in percent — we divide by 100 here so every downstream study
can assume decimal returns without second-guessing the source.

Uses `pandas_datareader.famafrench` which talks directly to the Dartmouth
zip archives. No credentials required — the data is public and free.
"""
from __future__ import annotations

import os
import pickle
from typing import Optional

import pandas as pd

from research._core import frozen as _frozen

CACHE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data_cache"
)


def _famafrench():
    """Return the pandas_datareader Ken French module, forced onto HTTPS.

    pandas_datareader hard-codes `http://` for the Dartmouth archive. Plain
    HTTP fails outright in any environment that only forwards HTTPS — which is
    most sandboxed and corporate networks — and it is unencrypted besides.
    The host serves the identical files over TLS, so switch the scheme once,
    here, rather than leaving every study to discover the failure separately.
    """
    from pandas_datareader import famafrench as ff
    if ff._URL.startswith("http://"):
        ff._URL = "https://" + ff._URL[len("http://"):]
    return ff


def _cached(name: str, builder):
    """Return the frozen panel if there is one; otherwise fetch and memoize.

    The frozen copy is checked first so a clone reproduces offline and is
    pinned against the upstream series being restated. See _core/frozen.py.
    """
    df = _frozen.load(name)
    if df is not None:
        return df
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{name}.pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    df = builder()
    with open(path, "wb") as f:
        pickle.dump(df, f)
    return df


def _normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    """Pandas-datareader returns a PeriodIndex at monthly frequency. Convert
    to month-end timestamps so it joins cleanly with yfinance-derived panels.
    """
    if isinstance(df.index, pd.PeriodIndex):
        df = df.copy()
        df.index = df.index.to_timestamp(how="end").normalize() + pd.offsets.MonthEnd(0)
    return df


def fetch_ff5(start: str = "2000-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Fetch the Fama-French 5-factor monthly series (MktRF/SMB/HML/RMW/CMA/RF).

    Columns match the Dartmouth naming convention:
        Mkt-RF, SMB, HML, RMW, CMA, RF
    All values are decimal returns.
    """
    def _build():
        ff = _famafrench()
        r = ff.FamaFrenchReader("F-F_Research_Data_5_Factors_2x3", start=start, end=end).read()
        df = r[0] / 100.0
        return _normalize_index(df)
    return _cached(f"ff5_{start}_{end or 'now'}", _build)


def fetch_ff_industries(n: int = 10, start: str = "2000-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Fetch Ken French's N-industry equal-weight portfolio returns.

    Supported n: 5, 10, 12, 17, 30, 38, 48, 49. We default to 10 because
    that's what the Kuant industry_rotation study uses for its canonical
    reference results.
    """
    assert n in {5, 10, 12, 17, 30, 38, 48, 49}, f"unsupported industry count: {n}"
    dataset = f"{n}_Industry_Portfolios"

    def _build():
        ff = _famafrench()
        r = ff.FamaFrenchReader(dataset, start=start, end=end).read()
        # Key 0 = average value-weighted returns -- monthly
        df = r[0] / 100.0
        return _normalize_index(df)
    return _cached(f"ff_{n}industry_{start}_{end or 'now'}", _build)


def fetch_ff_momentum_deciles(start: str = "2000-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Fetch the 10 prior-return momentum decile portfolios.

    Columns are named `Lo PRIOR`, `PRIOR 2` ... `PRIOR 9`, `Hi PRIOR` —
    keep that naming intact so the industry_rotation study can index them
    without renaming.
    """
    def _build():
        ff = _famafrench()
        r = ff.FamaFrenchReader("10_Portfolios_Prior_12_2", start=start, end=end).read()
        df = r[0] / 100.0
        return _normalize_index(df)
    return _cached(f"ff_10momentum_{start}_{end or 'now'}", _build)


def fetch_ff_op_portfolios(start: str = "2000-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Fetch the 5 portfolios formed on operating profitability (OP)."""
    def _build():
        ff = _famafrench()
        r = ff.FamaFrenchReader("Portfolios_Formed_on_OP", start=start, end=end).read()
        df = r[0] / 100.0
        return _normalize_index(df)
    return _cached(f"ff_op_portfolios_{start}_{end or 'now'}", _build)


def fetch_ff_inv_portfolios(start: str = "2000-01-01", end: Optional[str] = None) -> pd.DataFrame:
    """Fetch the 5 portfolios formed on investment (INV)."""
    def _build():
        ff = _famafrench()
        r = ff.FamaFrenchReader("Portfolios_Formed_on_INV", start=start, end=end).read()
        df = r[0] / 100.0
        return _normalize_index(df)
    return _cached(f"ff_inv_portfolios_{start}_{end or 'now'}", _build)
