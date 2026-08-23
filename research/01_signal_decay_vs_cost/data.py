"""Data layer with two backends: yfinance (default) or WRDS CRSP (optional).

The study's methodology is backend-agnostic — the same quintile-spread
cost-sweep code runs on either the 10-ETF yfinance universe (default)
or the full CRSP monthly universe (if you have WRDS creds in env).

yfinance backend:
    No credentials. Downloads the configured ticker list's adjusted close,
    resamples to month-end, returns a pct_change DataFrame.

WRDS backend:
    Requires WRDS_USERNAME / WRDS_PASSWORD. Queries CRSP monthly
    (`crsp.msf`) for the S&P 500 constituent set. It is a reference
    implementation, deliberately minimal: no delisting adjustment, no
    point-in-time constituent handling. Results from it are not published
    here — see the repository README on why the public backend is the
    published one.
"""
from __future__ import annotations

import os
from typing import List, Optional

import pandas as pd

from research._core import load_returns_panel


def load_yfinance_panel(
    tickers: List[str],
    start: str,
    end: Optional[str] = None,
    cache_name: Optional[str] = None,
) -> pd.DataFrame:
    """Delegates to the shared yfinance loader in `_core`."""
    return load_returns_panel(
        tickers=tickers,
        start=start,
        end=end,
        source="auto",
        cache_name=cache_name or f"sector_etf_{start}_{end or 'now'}",
    )


def load_wrds_crsp_monthly(
    start: str,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Pull CRSP monthly returns for the current S&P 500 constituent set.

    Returns a wide DataFrame: index=month-end, columns=permno (string),
    values=monthly returns. Requires WRDS_USERNAME / WRDS_PASSWORD env
    vars and the `wrds` Python package.
    """
    if not (os.environ.get("WRDS_USERNAME") and os.environ.get("WRDS_PASSWORD")):
        raise RuntimeError(
            "WRDS backend requested but WRDS_USERNAME / WRDS_PASSWORD are not "
            "set in the environment. Either export them, or run with "
            "`--source yfinance` (the default)."
        )
    try:
        import wrds
    except ImportError as e:
        raise RuntimeError(
            "WRDS backend requested but `wrds` package is not installed. "
            "`pip install wrds` and rerun."
        ) from e

    db = wrds.Connection(wrds_username=os.environ["WRDS_USERNAME"])
    try:
        query = f"""
            SELECT date, permno, ret
            FROM   crsp.msf
            WHERE  date BETWEEN '{start}' AND '{end or pd.Timestamp.today().date()}'
              AND  ret IS NOT NULL
        """
        df = db.raw_sql(query)
    finally:
        db.close()

    df["date"] = pd.to_datetime(df["date"])
    wide = df.pivot(index="date", columns="permno", values="ret")
    # Drop permno with < 24 observations to stabilize quintile ranks.
    wide = wide.loc[:, wide.notna().sum() >= 24]
    # Normalize to month-end stamps.
    wide.index = wide.index + pd.offsets.MonthEnd(0)
    return wide


def load_panel(source: str, cfg: dict) -> pd.DataFrame:
    """Dispatch based on --source flag / cfg."""
    if source == "yfinance":
        return load_yfinance_panel(
            tickers=list(cfg["universe"]),
            start=cfg["start_date"],
            end=cfg["end_date"],
        )
    if source == "wrds":
        return load_wrds_crsp_monthly(
            start=cfg["start_date"],
            end=cfg["end_date"],
        )
    raise ValueError(f"unknown source '{source}' — expected yfinance or wrds")
