# Frozen data

The inputs every study runs on, committed as CSV so a fresh clone reproduces
with **no network access at all**.

`MANIFEST.json` records, for each panel: the upstream source, the date it was
fetched, a SHA-256 of the file, its shape, and the range of dates it covers.

## Why the data is pinned and not just the config

Pinning a `config.yaml` fixes the parameters. It does not fix the data, and
three of the sources here can move underneath a published result:

- **yfinance** and **akshare** are unofficial endpoints. Their schema, their
  adjustment conventions, and how far back they serve can change without
  notice, and have.
- **Ken French** restates his series as CRSP data is revised.

So a figure published against a live fetch is reproducible only until the
upstream changes its mind. Freezing the panel removes that dependency: the
number in a study's `expected_output.json` is checkable against the exact
bytes it was computed from, by anyone, indefinitely.

## Working with it

```bash
python tools/freeze_data.py --verify    # checksum what is here, fetch nothing
python tools/freeze_data.py             # fetch and freeze anything missing
python tools/freeze_data.py --refresh   # re-fetch everything and re-freeze
```

A refresh is a deliberate act, not routine maintenance: it changes the inputs,
so every `expected_output.json` has to be regenerated and every figure quoted
in a README re-checked. `tools/rerun_and_diff.py` does both and prints the
list of prose that no longer matches.

`research/data_cache/` is a separate, unversioned working cache. If both exist
the frozen copy wins.

## Scope

What is committed here is a derived monthly (or daily, for study 09) return
matrix for a small, named universe — not a copy of any vendor's database. The
underlying sources and their terms are catalogued in
[`methodology/DATA_SOURCES.md`](../../methodology/DATA_SOURCES.md).
