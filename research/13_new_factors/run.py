#!/usr/bin/env python
"""New factors — FRED macro conditioners layered on price-based signals."""
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
    compute_metrics, split_is_oos, long_short_quintile_backtest,
    CostConfig, load_returns_panel,
)
from data import fetch_fred_macros  # noqa: E402
from signals import SIGNAL_REGISTRY  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rets = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"], end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] sector ETFs: {rets.shape}")

    print(f"[data] fetching FRED macros ({cfg['fred_series']}) ...")
    macros = fetch_fred_macros(cfg["fred_series"], cfg["start_date"], cfg["end_date"])
    print(f"[data] macros: {macros.shape}  {list(macros.columns)}")

    cost = CostConfig(**cfg["baseline_cost"])
    q = float(cfg["quantile"])

    results = {
        "config": {"n_months": int(rets.shape[0]), "macros_available": list(macros.columns)},
        "signals": {},
    }

    print("\n{:<15} {:>10} {:>10} {:>10} {:>10}".format(
        "signal", "full_SR", "IS_SR", "OOS_SR", "MDD"))
    for name in cfg["signals"]:
        sig = SIGNAL_REGISTRY[name](rets, macros)
        net, _ = long_short_quintile_backtest(sig, rets, quantile=q, cost_config=cost)
        full = compute_metrics(net, periods_per_year=12)
        iso = split_is_oos(net, split_date="2020-12-31", periods_per_year=12)
        results["signals"][name] = {"full": full, "is_oos": iso}
        print(f"{name:<15} {full['sharpe']:>+10.3f} {iso['is']['sharpe']:>+10.3f} "
              f"{iso['oos']['sharpe']:>+10.3f} {full['max_drawdown']:>+10.1%}")

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
