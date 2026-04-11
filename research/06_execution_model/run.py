#!/usr/bin/env python
"""Execution model — sweep seven cost regimes across four signals."""
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
    compute_metrics, long_short_quintile_backtest, CostConfig, load_returns_panel,
)
from signals import SIGNAL_REGISTRY  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rets = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"], end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] {rets.shape[0]} months x {rets.shape[1]} assets")

    q = float(cfg["quantile"])
    penalty = float(cfg["turnover_penalty"])

    base_sigs = {n: SIGNAL_REGISTRY[n](rets) for n in cfg["signals"]}

    results = {
        "config": {"n_months": int(rets.shape[0])},
        "grid": [],
    }

    # Build header: one row per scenario, one col per signal
    print("\n{:<18} {:>10} {:>10} {:>10} {:>10}".format(
        "scenario", *cfg["signals"]))
    for sc in cfg["scenarios"]:
        cost = CostConfig(
            commission_bps=float(sc["commission_bps"]),
            spread_bps=float(sc["spread_bps"]),
            impact_coeff=float(sc["impact_coeff"]),
            turnover_penalty=penalty,
        )
        row_by_signal = {}
        sharpes = []
        for name in cfg["signals"]:
            net, _ = long_short_quintile_backtest(
                base_sigs[name], rets, quantile=q, cost_config=cost
            )
            m = compute_metrics(net, periods_per_year=12)
            row_by_signal[name] = m
            sharpes.append(m["sharpe"])

        results["grid"].append({
            "scenario": sc["name"],
            "cost_config": {
                "commission_bps": sc["commission_bps"],
                "spread_bps": sc["spread_bps"],
                "impact_coeff": sc["impact_coeff"],
            },
            "by_signal": row_by_signal,
        })
        print(f"{sc['name']:<18} " + " ".join(f"{s:>+10.4f}" for s in sharpes))

    # Decomposition: baseline (no_cost) - crisis — the "cost drag"
    nocost_row = next(r for r in results["grid"] if r["scenario"] == "no_cost")
    crisis_row = next(r for r in results["grid"] if r["scenario"] == "crisis")
    decomp = {}
    for name in cfg["signals"]:
        nc = nocost_row["by_signal"][name]["sharpe"]
        cr = crisis_row["by_signal"][name]["sharpe"]
        decomp[name] = {
            "gross_sharpe_nocost": nc,
            "sharpe_at_crisis": cr,
            "cost_drag": round(nc - cr, 4),
        }
    results["cost_drag_decomposition"] = decomp

    print("\nCost drag (no_cost - crisis):")
    for name, d in decomp.items():
        print(f"  {name:<8}  gross={d['gross_sharpe_nocost']:+.3f} "
              f"crisis={d['sharpe_at_crisis']:+.3f} drag={d['cost_drag']:+.3f}")

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
    for new_row, old_row in zip(results["grid"], r["grid"]):
        if new_row["scenario"] != old_row["scenario"]:
            continue
        for name in new_row["by_signal"]:
            if name not in old_row["by_signal"]:
                continue
            a = new_row["by_signal"][name]; b = old_row["by_signal"][name]
            if abs(a["sharpe"] - b["sharpe"]) > 1e-3:
                failed.append((new_row["scenario"], name, a["sharpe"], b["sharpe"]))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
