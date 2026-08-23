"""Frozen data panels — the reason a clone of this repo reproduces offline.

Every study's input is a table with a DatetimeIndex. The first time the data is
fetched it is written here as a CSV under `research/_data_frozen/`, together
with a manifest recording where it came from, when, and its checksum. From then
on the fetchers read the frozen copy and never touch the network.

This exists because the upstream sources are not stable in the way a published
result needs them to be: yfinance and akshare are unofficial endpoints whose
schema and history can change without notice, and Ken French restates his
series. Pinning a config is not enough if the data underneath it moves — so the
data is pinned too, and `MANIFEST.json` says exactly what was pinned and when.

`tools/freeze_data.py` writes these files. Nothing else should.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Optional

import pandas as pd

FROZEN_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "_data_frozen"
)
MANIFEST = os.path.join(FROZEN_DIR, "MANIFEST.json")


def _path(name: str) -> str:
    return os.path.join(FROZEN_DIR, f"{name}.csv")


def available(name: str) -> bool:
    return os.path.exists(_path(name))


def load(name: str) -> Optional[pd.DataFrame]:
    """Return the frozen panel for `name`, or None if it was never frozen."""
    path = _path(name)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df.sort_index()


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def save(name: str, df: pd.DataFrame, source: str, fetched_at: str,
         note: str = "") -> dict:
    """Write a panel and record it in the manifest. Used only by the freezer."""
    os.makedirs(FROZEN_DIR, exist_ok=True)
    path = _path(name)
    df.sort_index().to_csv(path)

    entry = {
        "source": source,
        "fetched_at": fetched_at,
        "sha256": sha256(path),
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": [str(c) for c in df.columns],
        "first_obs": str(df.index.min().date()) if len(df) else None,
        "last_obs": str(df.index.max().date()) if len(df) else None,
        "note": note,
    }

    manifest = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
    manifest[name] = entry
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(manifest.items())), f, indent=2)
        f.write("\n")
    return entry


def verify() -> list:
    """Check every frozen file against the checksum recorded for it.

    Returns a list of problems; an empty list means the frozen data on disk is
    exactly what the manifest says it is.
    """
    if not os.path.exists(MANIFEST):
        return ["no MANIFEST.json — nothing has been frozen yet"]
    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    problems = []
    for name, entry in manifest.items():
        path = _path(name)
        if not os.path.exists(path):
            problems.append(f"{name}: in the manifest but the CSV is missing")
            continue
        actual = sha256(path)
        if actual != entry["sha256"]:
            problems.append(f"{name}: checksum mismatch "
                            f"(manifest {entry['sha256'][:12]}, file {actual[:12]})")
    for fn in sorted(os.listdir(FROZEN_DIR)) if os.path.isdir(FROZEN_DIR) else []:
        if fn.endswith(".csv") and fn[:-4] not in manifest:
            problems.append(f"{fn}: present but not in the manifest")
    return problems
