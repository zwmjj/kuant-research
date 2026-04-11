#!/usr/bin/env python
"""IS vs OOS Stability — entry point.

Runs the four reference signals from 01_signal_decay_vs_cost on the same
10-ETF universe, but instead of sweeping cost/penalty, this study focuses
on a single IS/OOS decomposition at 2020-12-31 and a set of rolling
3-year windows to answer: "which of these signals survived COVID / the
post-2021 regime change, and which didn't?"
"""
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
    compute_metrics,
    split_is_oos,
    rolling_windows,
    long_short_quintile_backtest,
    CostConfig,
    load_returns_panel,
)
from signals import SIGNAL_REGISTRY  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print(f"[data] loading {len(cfg['universe'])} sector ETFs via yfinance ...")
    returns = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"],
        end=cfg["end_date"],
        source="auto",
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] panel: {returns.shape[0]} months x {returns.shape[1]} assets")

    base = cfg["baseline_cost"]
    cost = CostConfig(
        commission_bps=base["commission_bps"],
        spread_bps=base["spread_bps"],
        impact_coeff=base["impact_coeff"],
        turnover_penalty=base["turnover_penalty"],
    )

    windows = [tuple(w) for w in cfg["rolling_windows"]]
    results = {
        "config": {
            "universe_size": returns.shape[1],
            "n_months": int(returns.shape[0]),
            "split_date": cfg["is_oos_split"],
        },
        "signals": {},
    }

    print("\n{:<8} {:>10} {:>10} {:>10} {:>10} {:>10}".format(
        "signal", "full_SR", "IS_SR", "OOS_SR", "Δ", "decay%"))
    for name in cfg["signals"]:
        sig_fn = SIGNAL_REGISTRY[name]
        sig = sig_fn(returns)
        net, _ = long_short_quintile_backtest(
            sig, returns, quantile=float(cfg["quantile"]), cost_config=cost,
        )
        full = compute_metrics(net, periods_per_year=12)
        iso = split_is_oos(net, split_date=cfg["is_oos_split"], periods_per_year=12)
        rolling = rolling_windows(net, windows, periods_per_year=12)

        # Stability decomposition — use absolute delta (OOS - IS) as the
        # primary stability metric. Relative decay-% is unstable when IS
        # is near zero, so we only compute it when |IS| > 0.1 (a
        # meaningful Sharpe) and otherwise report it as None.
        is_sr = iso["is"]["sharpe"]
        oos_sr = iso["oos"]["sharpe"]
        delta = round(oos_sr - is_sr, 4)
        decay_pct = round((oos_sr - is_sr) / abs(is_sr), 4) if abs(is_sr) > 0.1 else None

        results["signals"][name] = {
            "full": full,
            "is_oos": iso,
            "rolling": rolling,
            "oos_minus_is": delta,
            "oos_decay_vs_is_pct": decay_pct,
        }
        decay_str = f"{decay_pct:+.2%}" if decay_pct is not None else "n/a"
        print(f"{name:<8} {full['sharpe']:>+10.4f} {is_sr:>+10.4f} {oos_sr:>+10.4f} "
              f"{delta:>+10.4f} {decay_str:>10}")

    # ── write + summarize + repro gate ──
    out_dir = HERE / "sample_output"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    summary_lines = ["IS vs OOS STABILITY", ""]
    summary_lines.append(
        f"{'signal':<8} {'full_SR':>10} {'IS_SR':>10} {'OOS_SR':>10} {'Δ':>10}"
    )
    for name, sr in results["signals"].items():
        is_sr = sr["is_oos"]["is"]["sharpe"]
        oos_sr = sr["is_oos"]["oos"]["sharpe"]
        delta = sr["oos_minus_is"]
        summary_lines.append(
            f"{name:<8} {sr['full']['sharpe']:>+10.4f} {is_sr:>+10.4f} {oos_sr:>+10.4f} "
            f"{delta:>+10.4f}"
        )
    summary = "\n".join(summary_lines)
    with open(out_dir / "summary.txt", "w", encoding="utf-8") as f:
        f.write(summary + "\n")

    _repro_check(results)
    return results


def _repro_check(results):
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
        for metric in ("full", ):
            a = results["signals"][name][metric]
            b = ref["signals"][name][metric]
            for m in ("sharpe", "cagr", "max_drawdown"):
                if abs(a.get(m, 0) - b.get(m, 0)) > 1e-3:
                    failed.append((name, m, a.get(m), b.get(m)))
                checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked} checks failed:")
        for name, m, a, b in failed:
            print(f"  {name}.{m}: got {a:.4f} expected {b:.4f}")
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
