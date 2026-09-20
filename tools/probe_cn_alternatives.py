#!/usr/bin/env python3
"""Find a continuous source for the two A-share style indices that end early.

Study 10 has a hole. Six of its eight series run to 2025-12, but:

    LowVol   (sh000803)   2012-02 .. 2016-06   53 months
    Dividend (sh000922)   2010-01 .. 2019-01  109 months

Both terminate before the study's own 2020-12-31 IS/OOS split, so neither has
an out-of-sample figure and neither is comparable with the rest of the table.
The study says so, and says that fixing it needs a different data source
rather than a re-run.

This script is the diagnostic for that: it asks akshare, baostock and Tushare
the same question — can you give me continuous monthly history for these two
indices from 2010 to today? — and prints what each actually returns. It makes
no change to the repository. Run it on a machine with network access:

    python tools/probe_cn_alternatives.py
    TUSHARE_TOKEN=xxxx python tools/probe_cn_alternatives.py

Whatever wins, wire it into research/_data/fetch_cn.py, re-freeze, and re-run
study 10 — its README conclusions about LowVol_CN and Div_CN change with it.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

TARGETS = {
    "LowVol":   {"akshare": "sh000803", "tushare": "000803.SH", "baostock": "sh.000803"},
    "Dividend": {"akshare": "sh000922", "tushare": "000922.SH", "baostock": "sh.000922"},
}
START = "2010-01-01"


def describe(label: str, provider: str, s: pd.Series | None, note: str = ""):
    if s is None or len(s) == 0:
        print(f"  {label:9s} {provider:9s} —  {note or 'no data'}")
        return
    s = s.dropna().sort_index()
    months = s.resample("ME").last().dropna()
    gaps = months.index.to_series().diff().dt.days.gt(45).sum()
    print(f"  {label:9s} {provider:9s} {len(months):4d} months  "
          f"{months.index.min().date()} .. {months.index.max().date()}  "
          f"gaps>45d: {gaps}  {note}")


def try_akshare():
    print("\nakshare (current source)")
    try:
        import akshare as ak
    except ImportError:
        print("  not installed — pip install akshare")
        return
    for label, ids in TARGETS.items():
        try:
            raw = ak.stock_zh_index_daily(symbol=ids["akshare"])
            raw["date"] = pd.to_datetime(raw["date"])
            describe(label, "akshare", raw.set_index("date")["close"])
        except Exception as e:
            describe(label, "akshare", None, f"error: {str(e)[:70]}")


def try_baostock():
    print("\nbaostock (free, no token)")
    try:
        import baostock as bs
    except ImportError:
        print("  not installed — pip install baostock")
        return
    lg = bs.login()
    if lg.error_code != "0":
        print(f"  login failed: {lg.error_msg}")
        return
    try:
        for label, ids in TARGETS.items():
            rs = bs.query_history_k_data_plus(
                ids["baostock"], "date,close", start_date=START,
                frequency="m", adjustflag="3")
            if rs.error_code != "0":
                describe(label, "baostock", None, f"error: {rs.error_msg}")
                continue
            rows = []
            while rs.next():
                rows.append(rs.get_row_data())
            if not rows:
                describe(label, "baostock", None, "empty result — index likely not covered")
                continue
            df = pd.DataFrame(rows, columns=["date", "close"])
            df["date"] = pd.to_datetime(df["date"])
            describe(label, "baostock", df.set_index("date")["close"].astype(float))
    finally:
        bs.logout()


def try_tushare():
    token = os.environ.get("TUSHARE_TOKEN")
    print("\nTushare" + ("" if token else " — no TUSHARE_TOKEN set, skipping"))
    if not token:
        return
    try:
        import tushare as ts
    except ImportError:
        print("  not installed — pip install tushare")
        return
    pro = ts.pro_api(token)
    for label, ids in TARGETS.items():
        try:
            df = pro.index_daily(ts_code=ids["tushare"],
                                 start_date=START.replace("-", ""),
                                 end_date=pd.Timestamp.today().strftime("%Y%m%d"))
            if df is None or df.empty:
                describe(label, "tushare", None, "empty — may need more points for this index")
                continue
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            describe(label, "tushare", df.set_index("trade_date")["close"].sort_index())
        except Exception as e:
            describe(label, "tushare", None, f"error: {str(e)[:70]}")


def main():
    print(__doc__.split("This script")[0].strip())
    print("\nwanted: continuous monthly history, 2010-01 .. today, no gaps")
    try_akshare()
    try_baostock()
    try_tushare()
    print("\nPick the provider that returns continuous history for BOTH indices. "
          "If none does, the honest move is to drop the two series from study 10 "
          "rather than keep publishing a 2016 window next to 2025 ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
