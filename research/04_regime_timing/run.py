#!/usr/bin/env python
"""Regime timing — scale signal exposure by VIX regime, test 5 rules."""
from __future__ import annotations

import json
import os
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CACHE_DIR = str(REPO_ROOT / "research" / "data_cache")
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402

from research._core import (  # noqa: E402
    compute_metrics, long_short_quintile_backtest, CostConfig, load_returns_panel,
)
from signals import SIGNAL_REGISTRY, vix_regime, apply_rule  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rets = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"], end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] sector ETF panel: {rets.shape[0]}x{rets.shape[1]}")

    # VIX series — frozen copy first, exactly like every other input. This
    # study used to fetch it live on every run, which quietly made it the one
    # study that could not reproduce offline and whose regime labels could
    # shift under a data revision without anything reporting it.
    from research._core import frozen as _frozen
    vix_key = f"vix_{cfg['regime_source']}_{cfg['start_date']}_{cfg['end_date']}"
    vix_panel = _frozen.load(vix_key)
    if vix_panel is None:
        import yfinance as yf
        print(f"[data] fetching {cfg['regime_source']} daily close for VIX regime ...")
        vix_raw = yf.download(cfg["regime_source"], start=cfg["start_date"],
                              end=cfg["end_date"], auto_adjust=True, progress=False)
        vix_panel = vix_raw[["Close"]].copy()
        vix_panel.columns = ["VIX"]
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(os.path.join(CACHE_DIR, f"{vix_key}.pkl"), "wb") as fh:
            pickle.dump(vix_panel, fh)
    else:
        print(f"[data] VIX from frozen panel ({len(vix_panel)} rows)")
    vix = vix_panel.iloc[:, 0]
    regime = vix_regime(vix, lookback_months=int(cfg["regime_lookback_months"]))
    print(f"[data] regime coverage: {(regime == 'high').sum()} high, "
          f"{(regime == 'low').sum()} low months")

    cost = CostConfig(**cfg["baseline_cost"])
    q = float(cfg["quantile"])

    results = {
        "config": {
            "n_months": int(rets.shape[0]),
            "regime_source": cfg["regime_source"],
        },
        "grid": {},
    }

    # For each signal × each rule, compute Sharpe
    print("\n{:<8} {:<16} {:>10} {:>10} {:>10}".format(
        "signal", "rule", "Sharpe", "CAGR", "MDD"))
    for sig_name in cfg["signals"]:
        sig_fn = SIGNAL_REGISTRY[sig_name]
        sig = sig_fn(rets)
        raw_net, _ = long_short_quintile_backtest(sig, rets, quantile=q, cost_config=cost)

        results["grid"][sig_name] = {}
        for rule in cfg["rules"]:
            scaled = apply_rule(raw_net, regime, rule)
            m = compute_metrics(scaled.dropna(), periods_per_year=12)
            results["grid"][sig_name][rule] = m
            print(f"{sig_name:<8} {rule:<16} {m['sharpe']:>+10.4f} "
                  f"{m['cagr']:>+10.2%} {m['max_drawdown']:>+10.2%}")

    # Delta vs full-exposure baseline per signal
    deltas = {}
    for sig_name in cfg["signals"]:
        base = results["grid"][sig_name]["full"]["sharpe"]
        deltas[sig_name] = {
            rule: round(results["grid"][sig_name][rule]["sharpe"] - base, 4)
            for rule in cfg["rules"]
        }
    results["sharpe_minus_full"] = deltas

    print("\nSharpe delta vs `full` (no regime timing):")
    for sig_name, rule_deltas in deltas.items():
        print(f"  {sig_name}:")
        for rule, d in rule_deltas.items():
            print(f"    {rule:<16} {d:>+.4f}")

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
    for sig_name, rules in results["grid"].items():
        if sig_name not in r["grid"]:
            continue
        for rule, stats in rules.items():
            if rule not in r["grid"][sig_name]:
                continue
            for k in ("sharpe", "cagr"):
                a = stats[k]; b = r["grid"][sig_name][rule][k]
                if abs(a - b) > 1e-3:
                    failed.append((sig_name, rule, k, a, b))
                checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
