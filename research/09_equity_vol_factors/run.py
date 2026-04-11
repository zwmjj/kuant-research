#!/usr/bin/env python
"""Equity vol factor study — five vol-based factors on a 20-ETF universe."""
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
from data import load_daily_panel  # noqa: E402
from signals import SIGNAL_REGISTRY  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print(f"[data] loading daily panel ({len(cfg['universe'])} tickers) ...")
    daily = load_daily_panel(
        list(cfg["universe"]), cfg["start_date"], cfg["end_date"]
    )
    # Restrict to tickers with enough history
    daily = daily.dropna(thresh=int(0.5 * len(daily)), axis=1)
    print(f"[data] daily panel: {daily.shape[0]} days x {daily.shape[1]} assets")

    # Monthly forward returns for the quintile engine
    monthly_rets = (1 + daily).resample("ME").prod() - 1

    cost = CostConfig(**cfg["baseline_cost"])
    q = float(cfg["quantile"])
    results = {
        "config": {"n_days": int(daily.shape[0]), "n_months": int(monthly_rets.shape[0])},
        "signals": {},
    }

    print("\n{:<14} {:>8} {:>8} {:>8} {:>8}".format(
        "signal", "full_SR", "IS_SR", "OOS_SR", "MDD"))
    for name in cfg["signals"]:
        sig = SIGNAL_REGISTRY[name](daily)
        net, _ = long_short_quintile_backtest(sig, monthly_rets, quantile=q, cost_config=cost)
        full = compute_metrics(net, periods_per_year=12)
        iso = split_is_oos(net, split_date=cfg["is_oos_split"], periods_per_year=12)
        results["signals"][name] = {"full": full, "is_oos": iso}
        print(f"{name:<14} {full['sharpe']:>+8.3f} {iso['is']['sharpe']:>+8.3f} "
              f"{iso['oos']['sharpe']:>+8.3f} {full['max_drawdown']:>+8.1%}")

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
    for name, val in results["signals"].items():
        if name not in r["signals"]:
            continue
        a = val["full"]; b = r["signals"][name]["full"]
        for k in ("sharpe", "cagr", "max_drawdown"):
            if abs(a[k] - b[k]) > 1e-3:
                failed.append((name, k, a[k], b[k]))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
