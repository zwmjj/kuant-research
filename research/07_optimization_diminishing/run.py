#!/usr/bin/env python
"""Optimization diminishing returns — compare 4 allocation methods
applied to the same 4 signal-level return streams."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from research._core import (  # noqa: E402
    compute_metrics, long_short_quintile_backtest, CostConfig, load_returns_panel,
)
from signals import SIGNAL_REGISTRY, METHOD_REGISTRY  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rets = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"], end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] {rets.shape[0]} months x {rets.shape[1]} assets")

    # Step 1: build each signal's quintile L/S return stream.
    cost = CostConfig()  # default
    strategy_streams = {}
    for name in cfg["signals"]:
        sig = SIGNAL_REGISTRY[name](rets)
        net, _ = long_short_quintile_backtest(sig, rets, cost_config=cost)
        strategy_streams[name] = net

    strategies = pd.DataFrame(strategy_streams).dropna(how="all")
    print(f"[strat] 4-wide strategy stream: {strategies.shape[0]} months")

    # Step 2: for each allocation method, compute the portfolio return.
    lookback = int(cfg["lookback"])
    results = {
        "config": {
            "n_signals": len(cfg["signals"]),
            "n_months": int(strategies.shape[0]),
            "lookback": lookback,
        },
        "methods": {},
    }

    print("\n{:<18} {:>10} {:>10} {:>10}".format("method", "Sharpe", "CAGR", "MDD"))
    for method in cfg["methods"]:
        fn = METHOD_REGISTRY[method]
        if method == "equal_weight":
            port = fn(strategies)
        else:
            port = fn(strategies, lookback)
        m = compute_metrics(port.dropna(), periods_per_year=12)
        results["methods"][method] = m
        print(f"{method:<18} {m['sharpe']:>+10.4f} {m['cagr']:>+10.2%} {m['max_drawdown']:>+10.2%}")

    # Diminishing-returns delta: each method minus equal-weight
    ew_sharpe = results["methods"]["equal_weight"]["sharpe"]
    deltas = {
        m: round(v["sharpe"] - ew_sharpe, 4)
        for m, v in results["methods"].items()
    }
    results["sharpe_minus_equal_weight"] = deltas

    print("\nSharpe improvement over 1/N:")
    for m, d in deltas.items():
        print(f"  {m:<18} {d:>+.4f}")

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
    for m, stats in results["methods"].items():
        if m not in r["methods"]:
            continue
        old = r["methods"][m]
        for k in ("sharpe", "cagr", "max_drawdown"):
            if abs(stats[k] - old[k]) > 1e-3:
                failed.append((m, k, stats[k], old[k]))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
