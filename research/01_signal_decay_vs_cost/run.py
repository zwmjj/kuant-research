#!/usr/bin/env python
"""Signal decay vs transaction cost — entry point.

    python run.py                  # default: yfinance sector ETFs
    python run.py --source wrds    # full CRSP universe (needs WRDS creds)

Outputs go to sample_output/ and are diffed against expected_output.json
on each run (reproducibility gate).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402

from research._core import (  # noqa: E402
    compute_metrics,
    long_short_quintile_backtest,
    CostConfig,
)
from data import load_panel  # noqa: E402
from signals import build_signal, signal_autocorrelation  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("yfinance", "wrds"), default="yfinance")
    args = parser.parse_args()

    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # ── data ────────────────────────────────────────────────
    print(f"[data] loading panel via {args.source} ...")
    returns = load_panel(args.source, cfg)
    print(f"[data] panel: {returns.shape[0]} months x {returns.shape[1]} assets")

    results = {
        "config": {
            "source": args.source,
            "universe_size": returns.shape[1],
            "start": cfg["start_date"],
            "end": cfg["end_date"],
            "n_months": int(returns.shape[0]),
        },
    }

    # ── per-signal: turnover penalty sweep + autocorrelation ──
    penalty_grid = cfg["penalty_grid"]
    quantile = float(cfg["quantile"])
    baseline = cfg["baseline_cost"]

    signal_results = {}
    for sig_name in cfg["signals"]:
        print(f"\n[signal] {sig_name}")
        sig = build_signal(sig_name, returns)

        # Penalty sweep
        sweep = []
        for penalty in penalty_grid:
            cost = CostConfig(
                commission_bps=baseline["commission_bps"],
                spread_bps=baseline["spread_bps"],
                impact_coeff=baseline["impact_coeff"],
                turnover_penalty=float(penalty),
            )
            net, _ = long_short_quintile_backtest(sig, returns, quantile=quantile, cost_config=cost)
            m = compute_metrics(net, periods_per_year=12)
            sweep.append({
                "penalty": float(penalty),
                "sharpe": m["sharpe"],
                "cagr": m["cagr"],
                "max_drawdown": m["max_drawdown"],
            })
        best = max(sweep, key=lambda r: r["sharpe"])
        print(f"  penalty sweep: best penalty={best['penalty']:.2f} → Sharpe={best['sharpe']:+.4f}")

        # Cost multiplier sweep (at baseline penalty)
        cost_sweep = []
        for mult in cfg["cost_multipliers"]:
            cost = CostConfig(
                commission_bps=baseline["commission_bps"] * mult,
                spread_bps=baseline["spread_bps"] * mult,
                impact_coeff=baseline["impact_coeff"] * mult,
                turnover_penalty=baseline["turnover_penalty"],
            )
            net, _ = long_short_quintile_backtest(sig, returns, quantile=quantile, cost_config=cost)
            m = compute_metrics(net, periods_per_year=12)
            cost_sweep.append({
                "multiplier": float(mult),
                "sharpe": m["sharpe"],
                "cagr": m["cagr"],
            })
        print(f"  cost sweep: Sharpe at 1x={cost_sweep[1]['sharpe']:+.4f}, "
              f"5x={cost_sweep[-1]['sharpe']:+.4f}")

        # Autocorrelation
        acf = signal_autocorrelation(sig, max_lag=int(cfg["acf_lags"]))
        try:
            half = next(i + 1 for i, a in enumerate(acf) if a < 0.5)
        except StopIteration:
            half = len(acf)
        print(f"  autocorr: ACF@1={acf[0]:.3f}, half-life ≈ {half} months")

        signal_results[sig_name] = {
            "penalty_sweep": sweep,
            "best_penalty": best,
            "cost_multiplier_sweep": cost_sweep,
            "autocorrelation": acf,
            "half_life_months": int(half),
        }

    results["signals"] = signal_results

    # ── write + summarize + repro gate ──────────────────────
    out_dir = HERE / "sample_output"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    summary = _format_summary(results)
    print("\n" + summary)
    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(summary + "\n")

    _reproducibility_check(results)
    return results


def _format_summary(results):
    lines = ["SIGNAL DECAY VS COST", f"  universe: {results['config']['universe_size']} assets, "
             f"{results['config']['n_months']} months, source={results['config']['source']}", ""]
    lines.append(f"{'signal':<8} {'best_pen':>10} {'best_SR':>10} {'acf@1':>8} "
                 f"{'half_life':>10} {'SR@1x':>10} {'SR@5x':>10}")
    for name, sr in results["signals"].items():
        best = sr["best_penalty"]
        cost = sr["cost_multiplier_sweep"]
        lines.append(
            f"{name:<8} {best['penalty']:>10.2f} {best['sharpe']:>+10.4f} "
            f"{sr['autocorrelation'][0]:>+8.3f} {sr['half_life_months']:>10d} "
            f"{cost[1]['sharpe']:>+10.4f} {cost[-1]['sharpe']:>+10.4f}"
        )
    return "\n".join(lines)


def _reproducibility_check(results):
    ref_path = HERE / "expected_output.json"
    if not ref_path.exists():
        print("\n[repro] no expected_output.json — first run, commit results.json as reference.")
        return
    with open(ref_path, encoding="utf-8") as f:
        ref = json.load(f)
    checked, failed = 0, []
    for name in results.get("signals", {}):
        if name not in ref.get("signals", {}):
            continue
        a = results["signals"][name]["best_penalty"]
        b = ref["signals"][name]["best_penalty"]
        for metric in ("penalty", "sharpe"):
            if abs(a[metric] - b[metric]) > 1e-3:
                failed.append((name, metric, a[metric], b[metric]))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked} checks failed:")
        for name, metric, a, b in failed:
            print(f"  {name}.best_penalty.{metric}: got {a:.4f} expected {b:.4f}")
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
