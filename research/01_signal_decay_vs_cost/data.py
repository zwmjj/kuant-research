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

import numpy as np
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


def apply_delisting_adjustment(df: pd.DataFrame) -> pd.DataFrame:
    """Add `ret_adj`: the monthly return with the delisting return compounded in.

    Shumway (1997) convention. Expects columns `ret`, `dlret`, `dlstcd`, where
    `dlret`/`dlstcd` are NaN in every month except the delisting month.

        ret_adj = (1 + ret) * (1 + dlret) - 1

    A missing `dlret` in a delisting month is filled by reason, not dropped:
    -30% for a performance-related delisting (CRSP codes 500-599), 0% for
    M&A and exchange moves. Dropping the month instead is exactly the
    survivorship bias study 02 measures.

    Kept separate from the query so it can be tested without a WRDS session —
    see `research/_core/test_core.py`.
    """
    out = df.copy()
    is_delist = out["dlstcd"].notna()
    perf = out["dlstcd"].between(500, 599, inclusive="both")

    filled = out["dlret"].where(
        out["dlret"].notna(),
        pd.Series(np.where(perf, -0.30, 0.0), index=out.index).where(is_delist),
    )
    ret = out["ret"].fillna(0.0)
    out["ret_adj"] = np.where(filled.notna(), (1 + ret) * (1 + filled) - 1, out["ret"])
    return out


def load_wrds_crsp_monthly(
    start: str,
    end: Optional[str] = None,
    min_obs: int = 24,
) -> pd.DataFrame:
    """Pull delisting-adjusted CRSP monthly returns for the S&P 500 as it stood.

    Universe is **point-in-time**: membership comes from `crsp.msp500list`,
    which carries each permno's entry and exit dates, so a stock is in the
    panel only for the months it was actually in the index. Taking today's
    constituent list and running it backwards is the survivorship bias that
    study 02 is about, and it is worth several tenths of a Sharpe.

    Returns are delisting-adjusted on the Shumway (1997) convention, matching
    the treatment documented in `methodology/DATA_SOURCES.md`:

        ret_adj = (1 + ret) * (1 + dlret) - 1

    where the delisting return is compounded into the final month. Where
    `dlret` is missing, a performance-related delisting (codes 500-599) is
    assigned -30% and every other delisting 0%.

    Returns a wide DataFrame: index=month-end, columns=permno (string),
    values=monthly returns. Requires WRDS_USERNAME / WRDS_PASSWORD in the
    environment and the `wrds` package.

    NOTE ON STATUS: this backend is an interface, not a published result.
    Nothing in this repository is computed from it — every headline figure
    comes from the public yfinance backend, because a CRSP-backed number is
    not checkable by a reader without a subscription. The query below is
    written to standard CRSP schema but the repository ships no evidence that
    it ran; treat it as a starting point to adapt, not as a tested path.
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

    end = end or str(pd.Timestamp.today().date())

    db = wrds.Connection(wrds_username=os.environ["WRDS_USERNAME"])
    try:
        # msp500list gives (permno, start, ending) for index membership, so the
        # join keeps a stock only in the months it was a member. msenames adds
        # the standard US-common-stock screen. msedelist supplies the delisting
        # return, left-joined on the delisting month.
        query = f"""
            SELECT  msf.date,
                    msf.permno,
                    msf.ret,
                    dl.dlret,
                    dl.dlstcd
            FROM    crsp.msf                AS msf
            JOIN    crsp.msp500list         AS sp
                    ON  msf.permno = sp.permno
                    AND msf.date BETWEEN sp.start AND sp.ending
            JOIN    crsp.msenames           AS nm
                    ON  msf.permno = nm.permno
                    AND msf.date BETWEEN nm.namedt AND nm.nameendt
            LEFT JOIN crsp.msedelist        AS dl
                    ON  msf.permno = dl.permno
                    AND date_trunc('month', msf.date) = date_trunc('month', dl.dlstdt)
            WHERE   msf.date BETWEEN '{start}' AND '{end}'
              AND   nm.shrcd IN (10, 11)
              AND   nm.exchcd IN (1, 2, 3)
        """
        df = db.raw_sql(query, date_cols=["date"])
    finally:
        db.close()

    df = apply_delisting_adjustment(df)
    df = df.dropna(subset=["ret_adj"])
    wide = df.pivot_table(index="date", columns="permno", values="ret_adj")
    wide.columns = [str(c) for c in wide.columns]
    # Drop permno with too little history to stabilise quintile ranks.
    wide = wide.loc[:, wide.notna().sum() >= min_obs]
    wide.index = pd.to_datetime(wide.index) + pd.offsets.MonthEnd(0)
    return wide.sort_index()


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
