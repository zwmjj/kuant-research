#!/usr/bin/env python
"""Cross-market robustness — run identical 4 signals on US and CN
universes and compare Sharpe + correlation of the two return streams.
Answers: does the signal *methodology* generalize across markets?
"""
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
    compute_metrics, split_is_oos,
    long_short_quintile_backtest, CostConfig, load_returns_panel,
    correlation_matrix,
)
from research._data import fetch_cn_indices  # noqa: E402
from signals import SIGNAL_REGISTRY  # noqa: E402


def run_universe(label, rets, cfg, cost):
    print(f"\n[{label}] running 4 signals on {rets.shape[1]} assets, {rets.shape[0]} months")
    streams = {}
    stats = {}
    for name in cfg["signals"]:
        sig = SIGNAL_REGISTRY[name](rets)
        net, _ = long_short_quintile_backtest(
            sig, rets, quantile=float(cfg["quantile"]), cost_config=cost
        )
        streams[name] = net
        full = compute_metrics(net, periods_per_year=12)
        iso = split_is_oos(net, split_date=cfg["is_oos_split"], periods_per_year=12)
        stats[name] = {"full": full, "is_oos": iso}
        print(f"  {name:<8} Sharpe={full['sharpe']:+.3f}  "
              f"IS={iso['is']['sharpe']:+.3f}  OOS={iso['oos']['sharpe']:+.3f}")
    return streams, stats


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cost = CostConfig(**cfg["baseline_cost"])

    # US universe
    print("[data] US: loading sector ETFs via yfinance ...")
    us_rets = load_returns_panel(
        tickers=list(cfg["us_universe"]),
        start=cfg["start_date"], end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )

    # CN universe
    print("[data] CN: loading A-share indices via akshare ...")
    cn_panel = fetch_cn_indices(indices=cfg["cn_indices"], start=cfg["start_date"])
    cn_rets = cn_panel[(cn_panel.index >= cfg["start_date"]) & (cn_panel.index <= cfg["end_date"])]

    us_streams, us_stats = run_universe("US", us_rets, cfg, cost)
    cn_streams, cn_stats = run_universe("CN", cn_rets, cfg, cost)

    # Per-signal cross-market correlation — same signal, different universe
    print("\nCross-market correlation of same-signal streams:")
    per_signal_corr = {}
    for name in cfg["signals"]:
        us_s = us_streams[name].dropna()
        cn_s = cn_streams[name].dropna()
        common = us_s.index.intersection(cn_s.index)
        if len(common) < 12:
            per_signal_corr[name] = None
            continue
        corr = float(us_s.loc[common].corr(cn_s.loc[common]))
        per_signal_corr[name] = round(corr, 4)
        print(f"  US.{name} x CN.{name}: {corr:+.3f}  (n={len(common)})")

    # Sharpe consistency score: did the sign of each signal's Sharpe
    # match across US and CN? A good robustness check.
    sign_agree = []
    for name in cfg["signals"]:
        us_sh = us_stats[name]["full"]["sharpe"]
        cn_sh = cn_stats[name]["full"]["sharpe"]
        sign_agree.append({
            "signal": name,
            "us_sharpe": us_sh,
            "cn_sharpe": cn_sh,
            "same_sign": bool((us_sh > 0) == (cn_sh > 0)),
        })

    results = {
        "config": {
            "us_universe_size": us_rets.shape[1],
            "cn_universe_size": cn_rets.shape[1],
            "n_months_us": int(us_rets.shape[0]),
            "n_months_cn": int(cn_rets.shape[0]),
        },
        "us": us_stats,
        "cn": cn_stats,
        "per_signal_corr": per_signal_corr,
        "sign_agreement": sign_agree,
    }

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
    for market in ("us", "cn"):
        for name, val in results[market].items():
            if name not in r[market]:
                continue
            a = val["full"]; b = r[market][name]["full"]
            for k in ("sharpe", "cagr"):
                if abs(a[k] - b[k]) > 1e-3:
                    failed.append((market, name, k, a[k], b[k]))
                checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked}")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
