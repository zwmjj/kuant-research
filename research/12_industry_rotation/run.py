#!/usr/bin/env python
"""Industry Rotation research — entry point.

Run with:

    python run.py

Reads `config.yaml`, pulls Ken French industry data (cached after first
call), builds the L/S industry-momentum strategy and a couple of
reference factor premia, writes results to `sample_output/results.json`.
Compares to `expected_output.json` and reports any drift.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make the repo root importable so `research._core` / `research._data` resolve
# when running this script directly from its own folder.
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from research._core import compute_metrics, split_is_oos, rolling_windows  # noqa: E402
from research._data import (  # noqa: E402
    fetch_ff_industries,
    fetch_ff_momentum_deciles,
)
from research._data.fetch_ff import (  # noqa: E402
    fetch_ff_op_portfolios,
    fetch_ff_inv_portfolios,
)
from signals import (  # noqa: E402
    trailing_momentum,
    topn_bottomn_long_short,
    decile_hi_lo_spread,
    premium_hi_minus_lo,
)


def main():
    # ── config ──────────────────────────────────────────────
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    start = cfg["start_date"]
    end = cfg["end_date"]
    lookback = int(cfg["lookback_months"])
    top_n = int(cfg["top_n"])
    bottom_n = int(cfg["bottom_n"])
    universe = int(cfg["industry_universe"])
    split_date = cfg["is_oos_split"]
    windows = [tuple(w) for w in cfg["rolling_windows"]]

    print(f"[config] {universe}-industry universe, {lookback}m lookback, "
          f"{top_n}L/{bottom_n}S, {start} → {end}")

    # ── data ────────────────────────────────────────────────
    print("[data] fetching Ken French industry returns ...")
    industries = fetch_ff_industries(n=universe, start=start, end=end)
    industries = industries[(industries.index >= start) & (industries.index <= end)]
    print(f"[data] {industries.shape[0]} months x {industries.shape[1]} industries")

    # ── strategy ────────────────────────────────────────────
    print(f"[strat] {lookback}-month trailing momentum, long top {top_n}, short bottom {bottom_n}")
    mom = trailing_momentum(industries, lookback=lookback)
    ls_returns, legs = topn_bottomn_long_short(mom, industries, top_n, bottom_n)
    print(f"[strat] {len(ls_returns)} trading months")

    # ── metrics ─────────────────────────────────────────────
    results = {
        "config": {
            "universe": universe, "lookback": lookback,
            "top_n": top_n, "bottom_n": bottom_n,
            "start": start, "end": end,
            "split_date": split_date,
        },
        "industry_momentum": compute_metrics(ls_returns, periods_per_year=12),
        "industry_momentum_is_oos": split_is_oos(ls_returns, split_date=split_date, periods_per_year=12),
        "industry_momentum_rolling": rolling_windows(ls_returns, windows, periods_per_year=12),
    }

    # ── per-industry stats (plain long-only) ────────────────
    ind_stats = {}
    for col in industries.columns:
        ind_stats[str(col).strip()] = compute_metrics(industries[col], periods_per_year=12)
    results["industry_long_only"] = ind_stats

    # ── reference factor premia ─────────────────────────────
    if cfg.get("include_decile_spread"):
        print("[ref] decile momentum spread (Hi-Lo)")
        mom_dec = fetch_ff_momentum_deciles(start=start, end=end)
        mom_dec = mom_dec[(mom_dec.index >= start) & (mom_dec.index <= end)]
        spread = decile_hi_lo_spread(mom_dec)
        results["decile_hi_lo"] = compute_metrics(spread, periods_per_year=12)
        results["decile_hi_lo_is_oos"] = split_is_oos(spread, split_date=split_date, periods_per_year=12)

    if cfg.get("include_op_inv_premiums"):
        print("[ref] operating profitability / investment premia")
        op = fetch_ff_op_portfolios(start=start, end=end)
        inv = fetch_ff_inv_portfolios(start=start, end=end)
        op = op[(op.index >= start) & (op.index <= end)]
        inv = inv[(inv.index >= start) & (inv.index <= end)]
        results["op_premium"] = compute_metrics(premium_hi_minus_lo(op), periods_per_year=12)
        results["inv_premium"] = compute_metrics(-premium_hi_minus_lo(inv), periods_per_year=12)
        # inv is Lo - Hi (conservative investors win) so we negate the Hi-Lo output

    # ── write output + diff against expected ──────────────
    out_dir = HERE / "sample_output"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Human-readable summary
    summary = []
    m = results["industry_momentum"]
    summary.append("INDUSTRY MOMENTUM L/S")
    summary.append(f"  Sharpe={m['sharpe']:.3f}  CAGR={m['cagr']:.2%}  MDD={m['max_drawdown']:.2%}  n={m['n_periods']}")
    iso = results["industry_momentum_is_oos"]
    summary.append(f"  IS Sharpe={iso['is']['sharpe']:.3f}   OOS Sharpe={iso['oos']['sharpe']:.3f}")
    summary.append("")
    summary.append("ROLLING 3Y WINDOWS")
    for r in results["industry_momentum_rolling"]:
        summary.append(f"  {r['period']:10s}  Sharpe={r['sharpe']:+.3f}  cum={r['cum_return']:+.2%}")
    if "decile_hi_lo" in results:
        summary.append("")
        d = results["decile_hi_lo"]
        summary.append(f"DECILE (Hi-Lo): Sharpe={d['sharpe']:.3f}  CAGR={d['cagr']:.2%}")
    if "op_premium" in results:
        summary.append(f"OP  premium:   Sharpe={results['op_premium']['sharpe']:.3f}")
        summary.append(f"INV premium:   Sharpe={results['inv_premium']['sharpe']:.3f}")

    text = "\n".join(summary)
    print("\n" + text)
    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")

    _reproducibility_check(results)
    return results


def _reproducibility_check(results: dict):
    """Diff current run against expected_output.json if present."""
    ref_path = HERE / "expected_output.json"
    if not ref_path.exists():
        print("\n[repro] no expected_output.json yet — first run. "
              "Commit sample_output/results.json as the reference.")
        return

    with open(ref_path, encoding="utf-8") as f:
        ref = json.load(f)

    checked = 0
    failed = []
    for key in ("industry_momentum", "decile_hi_lo", "op_premium", "inv_premium"):
        if key not in ref or key not in results:
            continue
        for metric in ("sharpe", "cagr", "max_drawdown"):
            a = results[key].get(metric)
            b = ref[key].get(metric)
            if a is None or b is None:
                continue
            if abs(a - b) > 1e-3:
                failed.append((key, metric, a, b))
            checked += 1

    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked} checks failed:")
        for key, metric, a, b in failed:
            print(f"  {key}.{metric}: got {a:.4f} expected {b:.4f} (Δ={a-b:+.4f})")
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
