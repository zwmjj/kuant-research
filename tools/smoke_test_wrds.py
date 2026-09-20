#!/usr/bin/env python3
"""Prove the CRSP backend actually runs, over a deliberately small window.

The repository ships `research/01_signal_decay_vs_cost/data.py` with a CRSP
query written to standard schema but no evidence that it has ever executed.
That is currently stated plainly in three places. This script is how that
claim gets upgraded — or, if the query is wrong, how it gets found out.

    WRDS_USERNAME=... WRDS_PASSWORD=... python tools/smoke_test_wrds.py

It pulls two years, not twenty-five: enough to prove the joins resolve, the
column names are right, and the delisting left-join actually matches rows.
It publishes nothing and writes nothing. CRSP data cannot be redistributed,
so the outcome of this script is a change of wording, not a change of data.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

START, END = "2018-01-01", "2019-12-31"


def load_study01_data():
    path = REPO / "research" / "01_signal_decay_vs_cost" / "data.py"
    spec = importlib.util.spec_from_file_location("study01_data", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return ok


def main() -> int:
    if not (os.environ.get("WRDS_USERNAME") and os.environ.get("WRDS_PASSWORD")):
        print("WRDS_USERNAME / WRDS_PASSWORD not set — skipping.\n"
              "This step is optional; nothing else depends on it.")
        return 0

    print(f"Pulling CRSP {START} .. {END} through the study's own loader.\n"
          "A first WRDS connection can take a minute.\n")
    mod = load_study01_data()

    try:
        panel = mod.load_wrds_crsp_monthly(start=START, end=END, min_obs=12)
    except Exception as exc:
        print(f"  [FAIL] the query raised: {type(exc).__name__}: {exc}")
        print("\nThe backend does not run as written. Fix the query before changing "
              "any wording — the docs currently say it is unexercised, which is "
              "still the accurate description.")
        return 1

    print()
    ok = True
    ok &= check("returned a DataFrame", isinstance(panel, pd.DataFrame))
    ok &= check("non-empty", len(panel) > 0, f"{panel.shape[0]} rows x {panel.shape[1]} permno")
    ok &= check("monthly index at month-end",
                isinstance(panel.index, pd.DatetimeIndex)
                and bool((panel.index == panel.index + pd.offsets.MonthEnd(0)).all()))
    ok &= check("roughly 24 months", 20 <= len(panel) <= 26, f"{len(panel)} months")
    ok &= check("universe looks like the S&P 500, not all of CRSP",
                300 <= panel.shape[1] <= 900,
                f"{panel.shape[1]} permno — all of CRSP would be thousands")
    finite = panel.stack().dropna()
    ok &= check("returns are decimals, not percent",
                bool(finite.abs().quantile(0.99) < 1.0),
                f"99th pct |ret| = {finite.abs().quantile(0.99):.3f}")

    # Did the delisting join match anything at all? If it silently matched zero
    # rows the panel would look fine and the adjustment would be a no-op.
    try:
        import wrds
        db = wrds.Connection(wrds_username=os.environ["WRDS_USERNAME"])
        try:
            n = db.raw_sql(
                f"SELECT COUNT(*) AS n FROM crsp.msedelist "
                f"WHERE dlstdt BETWEEN '{START}' AND '{END}'"
            )["n"].iloc[0]
        finally:
            db.close()
        ok &= check("delisting table has rows in this window", int(n) > 0,
                    f"{int(n)} delisting events — the left-join has something to match")
    except Exception as exc:
        ok &= check("delisting table reachable", False, f"{type(exc).__name__}: {exc}")

    print()
    if not ok:
        print("Some checks failed. Leave the wording as 'unexercised' and fix the "
              "query first — an interface that half-works is worse than one "
              "labelled honestly.")
        return 1

    print("""All checks passed. The query runs and the joins resolve.

What to change, in these three places, from "ships unexercised" to a verified
but unpublished backend:

  research/01_signal_decay_vs_cost/data.py          (docstring, NOTE ON STATUS)
  research/01_signal_decay_vs_cost/data_contract.md (Status paragraph)
  research/01_signal_decay_vs_cost/README.md        (the CRSP hook paragraph)

Suggested wording:

  The query has been executed against WRDS over a two-year window and the
  joins resolve as written; no result from it is published here, because a
  CRSP-backed figure is not checkable by a reader without a subscription.

Do not weaken the second half. Whether it runs and whether a reader can check
it are different questions, and only the second one decides what gets
published.""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
