#!/usr/bin/env python
"""Multi-factor construction — blend k signals and measure Sharpe(k)."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402

from research._core import (  # noqa: E402
    compute_metrics, split_is_oos,
    long_short_quintile_backtest, CostConfig, load_returns_panel,
)
from signals import SIGNAL_REGISTRY, blend_signal_streams  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print(f"[data] 10 sector ETFs ...")
    rets = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"], end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] panel: {rets.shape[0]}x{rets.shape[1]}")

    cost = CostConfig(**cfg["baseline_cost"])
    q = float(cfg["quantile"])

    # Pre-compute all base signals once
    base = {n: SIGNAL_REGISTRY[n](rets) for n in cfg["signals"]}

    combos = []
    names = cfg["signals"]
    for k in range(1, len(names) + 1):
        for combo in itertools.combinations(names, k):
            combos.append(list(combo))

    results = {
        "config": {"universe_size": rets.shape[1], "n_months": int(rets.shape[0])},
        "combinations": [],
    }

    print("\n{:<30} {:>8} {:>8} {:>8}".format("combo", "k", "Sharpe", "OOS_SR"))
    for combo in combos:
        blended = blend_signal_streams(base, combo, zscale=True)
        net, _ = long_short_quintile_backtest(blended, rets, quantile=q, cost_config=cost)
        full = compute_metrics(net, periods_per_year=12)
        iso = split_is_oos(net, split_date=cfg["is_oos_split"], periods_per_year=12)
        row = {
            "signals": combo,
            "k": len(combo),
            "full": full,
            "is_oos": iso,
        }
        results["combinations"].append(row)
        print(f"{'+'.join(combo):<30} {len(combo):>8} {full['sharpe']:>+8.3f} "
              f"{iso['oos']['sharpe']:>+8.3f}")

    # Summary by k — average Sharpe of all combinations at each size
    summary_by_k = {}
    for k in range(1, len(names) + 1):
        rows = [r for r in results["combinations"] if r["k"] == k]
        if not rows:
            continue
        sharpes = [r["full"]["sharpe"] for r in rows]
        summary_by_k[k] = {
            "n_combinations": len(rows),
            "mean_sharpe": round(sum(sharpes) / len(sharpes), 4),
            "best_combo": max(rows, key=lambda r: r["full"]["sharpe"])["signals"],
            "best_sharpe": round(max(sharpes), 4),
        }
    results["summary_by_k"] = summary_by_k

    print("\nBy k (mean Sharpe across all k-wise blends):")
    for k, s in summary_by_k.items():
        print(f"  k={k}: mean={s['mean_sharpe']:+.4f}  "
              f"best={s['best_sharpe']:+.4f} ({'+'.join(s['best_combo'])})")

    out_dir = HERE / "sample_output"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    _repro_check(results)
    return results


def _repro_check(results):
    ref = HERE / "expected_output.json"
    if not ref.exists():
        print("\n[repro] no expected_output.json — first run, commit results.json as reference.")
        return
    with open(ref, encoding="utf-8") as f:
        r = json.load(f)
    checked, failed = 0, []
    for new, old in zip(results["combinations"], r["combinations"]):
        if new["signals"] != old["signals"]:
            continue
        for k in ("sharpe", "cagr"):
            if abs(new["full"][k] - old["full"][k]) > 1e-3:
                failed.append(("+".join(new["signals"]), k, new["full"][k], old["full"][k]))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
