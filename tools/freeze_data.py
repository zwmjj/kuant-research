#!/usr/bin/env python3
"""Fetch every study's input once, and commit it, so the repo reproduces offline.

Run this on a machine with network access:

    python tools/freeze_data.py            # fetch what is missing, then freeze
    python tools/freeze_data.py --refresh  # re-fetch and re-freeze everything
    python tools/freeze_data.py --verify   # checksum the frozen files, fetch nothing

What it does
------------
1. Runs each study once. Their fetchers fill `research/data_cache/*.pkl`.
2. Writes every cached panel out as a CSV under `research/_data_frozen/`,
   with a `MANIFEST.json` entry recording the upstream source, the fetch date,
   a SHA-256, the shape, and the date range covered.
3. Round-trips each CSV back through the reader and asserts it is numerically
   identical to what was fetched, so freezing never silently changes a number.

After this, `research/_data_frozen/` is committed and every study reads it
instead of the network. That is what pins a published figure: the config alone
cannot do it, because yfinance and akshare serve unofficial endpoints whose
history can change, and Ken French restates his series.

Redistribution note: what is committed here is a derived monthly return matrix
for a small named universe, not a bulk copy of any vendor's database. Check the
terms of any source before adding one that is licensed rather than public.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pickle
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research._core import frozen  # noqa: E402

CACHE = REPO / "research" / "data_cache"
STUDIES = sorted(p for p in (REPO / "research").glob("[0-9][0-9]_*") if p.is_dir())

# Cache-key prefix -> upstream source, for the manifest.
SOURCES = [
    ("sector_etf_", "Yahoo Finance via yfinance — monthly total returns, US sector ETFs"),
    ("hk_",         "Yahoo Finance via yfinance — monthly total returns, HK large caps"),
    ("etf_daily_",  "Yahoo Finance via yfinance — daily adjusted closes"),
    ("ff5_",        "Kenneth French Data Library — FF5 monthly factors"),
    ("ff_",         "Kenneth French Data Library — portfolio sorts"),
    ("cn_",         "akshare — A-share style index levels (Sina/Tencent endpoint)"),
    ("fred_",       "FRED (Federal Reserve Bank of St. Louis) — daily macro series"),
]


def source_of(name: str) -> str:
    for prefix, label in SOURCES:
        if name.startswith(prefix):
            return label
    return "unknown — add a prefix to SOURCES in tools/freeze_data.py"


def run_studies(timeout: int):
    ok, failed = [], []
    for d in STUDIES:
        print(f"  running {d.name} ...", flush=True)
        try:
            p = subprocess.run([sys.executable, "run.py"], cwd=d,
                               capture_output=True, text=True, timeout=timeout)
            (ok if p.returncode == 0 else failed).append(d.name)
            if p.returncode != 0:
                tail = "\n".join((p.stdout + p.stderr).strip().splitlines()[-4:])
                print(f"    exit {p.returncode}\n      {tail}")
        except subprocess.TimeoutExpired:
            failed.append(d.name)
            print(f"    TIMEOUT after {timeout}s")
    return ok, failed


def freeze_all(refresh: bool) -> int:
    if not CACHE.is_dir():
        print("No research/data_cache/ — nothing was fetched. "
              "Check the study logs above for the data-source error.")
        return 1

    today = dt.date.today().isoformat()
    written, skipped, problems = 0, 0, []

    for pkl in sorted(CACHE.glob("*.pkl")):
        name = pkl.stem
        if frozen.available(name) and not refresh:
            skipped += 1
            continue
        with open(pkl, "rb") as f:
            df = pickle.load(f)
        if not isinstance(df, pd.DataFrame):
            problems.append(f"{name}: cached object is {type(df).__name__}, not a DataFrame")
            continue

        entry = frozen.save(name, df, source=source_of(name), fetched_at=today)

        # Round-trip: the frozen CSV must reproduce the fetched panel exactly.
        # Index *resolution* is excluded deliberately — a CSV carries no dtype,
        # so the reader picks one, and s/us/ns are the same instants. Every
        # value, every column and every date is still compared exactly.
        back = frozen.load(name)
        try:
            ref = df.sort_index().copy()
            ref.index = pd.to_datetime(ref.index).as_unit("ns")
            pd.testing.assert_frame_equal(
                ref, back, check_freq=False, check_dtype=False,
                check_index_type=False, atol=0, rtol=1e-12
            )
        except AssertionError as exc:
            problems.append(f"{name}: CSV round-trip changed the data\n    {str(exc)[:200]}")
            continue

        written += 1
        print(f"  froze {name}  [{entry['rows']}x{entry['cols']}] "
              f"{entry['first_obs']} .. {entry['last_obs']}")

    print(f"\nfroze {written}, already frozen {skipped}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  " + p)
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="re-fetch and overwrite panels that are already frozen")
    ap.add_argument("--verify", action="store_true",
                    help="only checksum what is already frozen; fetch nothing")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    if args.verify:
        problems = frozen.verify()
        if problems:
            print("frozen data does NOT match the manifest:")
            for p in problems:
                print("  " + p)
            return 1
        print("frozen data matches MANIFEST.json")
        return 0

    if args.refresh and CACHE.is_dir():
        for f in CACHE.glob("*.pkl"):
            f.unlink()
        print("cleared research/data_cache/ — every panel will be re-fetched\n")

    print("=== running studies to populate the cache ===")
    ok, failed = run_studies(args.timeout)
    print(f"\nstudies ok: {len(ok)}   failed: {failed or 'none'}")
    if failed:
        print("A study that failed contributed no data; its panels will be missing "
              "from the freeze. Fix the data-source error and re-run.")

    print("\n=== freezing ===")
    rc = freeze_all(args.refresh)

    print("\n=== verifying ===")
    problems = frozen.verify()
    for p in problems:
        print("  " + p)
    if not problems:
        print("  all frozen files match their checksums")

    print("\nNext: commit research/_data_frozen/, then confirm a clean clone "
          "reproduces with no network by running any study with the network off.")
    return rc or (1 if problems or failed else 0)


if __name__ == "__main__":
    raise SystemExit(main())
