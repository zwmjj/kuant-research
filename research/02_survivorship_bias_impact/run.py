#!/usr/bin/env python
"""Survivorship bias — synthetic demonstration."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402

from research._core import (  # noqa: E402
    compute_metrics, split_is_oos, long_short_quintile_backtest, CostConfig,
)
from signals import generate_universe_with_delisting, signal_mom12  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print(f"[gen] synthetic universe: {cfg['n_assets']} assets x {cfg['n_months']} months")
    print(f"[gen] delisting prob/month={cfg['delist_prob_per_month']}, "
          f"terminal return ~ N({cfg['delist_return_mean']}, {cfg['delist_return_std']})")

    survivors, full, events = generate_universe_with_delisting(
        n_assets=int(cfg["n_assets"]),
        n_months=int(cfg["n_months"]),
        seed=int(cfg["random_seed"]),
        delist_prob_per_month=float(cfg["delist_prob_per_month"]),
        delist_return_mean=float(cfg["delist_return_mean"]),
        delist_return_std=float(cfg["delist_return_std"]),
        min_life_months=int(cfg["min_life_months"]),
    )
    print(f"[gen] events: {len(events)} delistings "
          f"({len(events)/cfg['n_assets']:.0%} of the universe)")
    print(f"[gen] survivors panel: {survivors.shape}  full panel: {full.shape}")

    cost = CostConfig(**cfg["baseline_cost"])
    q = float(cfg["quantile"])

    results = {
        "config": {
            "n_assets": int(cfg["n_assets"]),
            "n_months": int(cfg["n_months"]),
            "n_delistings": len(events),
        },
        "delistings": events[:20],  # keep first 20 for inspection
    }

    print("\n{:<24} {:>10} {:>10} {:>10}".format("panel", "Sharpe", "CAGR", "MDD"))
    for label, panel in [
        ("survivors_only", survivors),
        ("full_delist_adjusted", full),
    ]:
        sig = signal_mom12(panel)
        net, _ = long_short_quintile_backtest(sig, panel, quantile=q, cost_config=cost)
        m = compute_metrics(net.dropna(), periods_per_year=12)
        results[label] = m
        print(f"{label:<24} {m['sharpe']:>+10.4f} {m['cagr']:>+10.2%} {m['max_drawdown']:>+10.2%}")

    # The bias
    gap = results["survivors_only"]["sharpe"] - results["full_delist_adjusted"]["sharpe"]
    results["survivorship_bias_sharpe_gap"] = round(gap, 4)
    print(f"\nSurvivorship bias (Sharpe inflation): {gap:+.4f}")

    out_dir = HERE / "sample_output"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    _repro_check(results)
    return results


def _repro_check(results):
    ref = HERE / "expected_output.json"
    if not ref.exists():
        print("\n[repro] no expected_output.json — first run.")
        return
    with open(ref, encoding="utf-8") as f:
        r = json.load(f)
    checked, failed = 0, []
    for label in ("survivors_only", "full_delist_adjusted"):
        if label not in r:
            continue
        a = results[label]; b = r[label]
        for k in ("sharpe", "cagr", "max_drawdown"):
            if abs(a[k] - b[k]) > 1e-3:
                failed.append((label, k, a[k], b[k]))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
