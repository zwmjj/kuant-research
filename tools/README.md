# tools

Maintenance scripts. Nothing here is imported by a study; nothing here runs as
part of a normal `python run.py`.

| Script | What it does |
|---|---|
| `freeze_data.py` | Fetches every study's input once and commits it under `research/_data_frozen/`, with a manifest and checksums, so the repository reproduces offline. `--verify` checksums without fetching. |
| `rerun_and_diff.py` | Re-runs all 14 studies, diffs **every** numeric leaf against the committed `expected_output.json` — not just the handful each study's own gate checks — and then reports which lines of prose quote a figure that moved. `--accept` refreshes the reference outputs. |
| `smoke_test_wrds.py` | Pulls two years through study 01's CRSP loader to prove the query executes and the joins resolve — including that the delisting left-join matches rows rather than silently matching none. Publishes nothing; the outcome is a change of wording, not of data. Skips itself when no WRDS credentials are set. |
| `probe_cn_alternatives.py` | Diagnostic for the hole in study 10: asks akshare, baostock and Tushare whether any of them serves continuous history for the two A-share style indices whose series end in 2016 and 2019. Changes nothing; prints what each provider actually returns. |
| `bootstrap_offline.sh` | Runs the unit tests, then the freeze, then the re-run, in that order. This is the one-pass version for a machine that has network access. |

The core has its own offline test suite:

```bash
python research/_core/test_core.py
```

It constructs its own inputs and asserts against hand-derived values, so it
runs anywhere and needs no data.
