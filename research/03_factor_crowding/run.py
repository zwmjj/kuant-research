#!/usr/bin/env python
"""Factor Crowding — run four signals and FF5-regress each one's return
stream to decompose alpha from systematic factor exposures."""
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
    long_short_quintile_backtest,
    CostConfig,
    load_returns_panel,
    ff5_regression,
    correlation_matrix,
)
from research._data import fetch_ff5  # noqa: E402
from signals import SIGNAL_REGISTRY  # noqa: E402


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print(f"[data] loading {len(cfg['universe'])} sector ETFs ...")
    rets = load_returns_panel(
        tickers=list(cfg["universe"]),
        start=cfg["start_date"],
        end=cfg["end_date"],
        cache_name=f"sector_etf_{cfg['start_date']}_{cfg['end_date']}",
    )
    print(f"[data] panel: {rets.shape[0]} months x {rets.shape[1]} assets")

    print("[data] fetching FF5 factors from Dartmouth ...")
    ff5 = fetch_ff5(start=cfg["start_date"], end=cfg["end_date"])
    print(f"[data] FF5: {ff5.shape[0]} months")

    base = cfg["baseline_cost"]
    cost = CostConfig(**base)
    q = float(cfg["quantile"])

    results = {
        "config": {"universe_size": rets.shape[1], "n_months": int(rets.shape[0])},
        "signals": {},
    }

    signal_streams = {}
    print("\n{:<8} {:>7} {:>10} {:>8} {:>8} {:>8} {:>8} {:>8} {:>6}".format(
        "signal", "Sharpe", "alpha_ann", "a_t", "b_mkt", "b_smb", "b_hml", "b_rmw", "R2"))
    for name in cfg["signals"]:
        sig = SIGNAL_REGISTRY[name](rets)
        net, _ = long_short_quintile_backtest(sig, rets, quantile=q, cost_config=cost)
        signal_streams[name] = net

        m = compute_metrics(net, periods_per_year=12)
        reg = ff5_regression(net, ff5, periods_per_year=12)
        results["signals"][name] = {
            "performance": m,
            "ff5_regression": reg,
        }

        if "error" not in reg:
            print(f"{name:<8} {m['sharpe']:>+7.3f} {reg['alpha']:>+10.4f} "
                  f"{reg['alpha_t']:>+8.2f} {reg['beta_mkt']:>+8.3f} "
                  f"{reg['beta_smb']:>+8.3f} {reg['beta_hml']:>+8.3f} "
                  f"{reg['beta_rmw']:>+8.3f} {reg['r2']:>+6.3f}")
        else:
            print(f"{name:<8} regression skipped: {reg['error']}")

    # Correlation between the four strategies (crowding check)
    corr = correlation_matrix(pd.DataFrame(signal_streams).dropna(how="all"))
    results["strategy_correlation"] = corr

    print("\nStrategy correlation matrix:")
    labels = corr["labels"]
    for i, row_label in enumerate(labels):
        row_vals = "  ".join(f"{v:+.3f}" for v in corr["values"][i])
        print(f"  {row_label:<8} {row_vals}")

    # ── outputs ──
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
    for name, val in results["signals"].items():
        if name not in r["signals"]:
            continue
        a = val["performance"]; b = r["signals"][name]["performance"]
        for k in ("sharpe", "cagr", "max_drawdown"):
            if abs(a[k] - b[k]) > 1e-3:
                failed.append((name, k, a[k], b[k]))
            checked += 1
        ra = val["ff5_regression"]; rb = r["signals"][name]["ff5_regression"]
        if "error" not in ra and "error" not in rb:
            for k in ("alpha", "r2", "beta_mkt"):
                if abs(ra[k] - rb[k]) > 1e-3:
                    failed.append((f"{name}.reg", k, ra[k], rb[k]))
                checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked} checks failed")
        for row in failed: print(" ", row)
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    import pandas as pd  # noqa: E402 — needed above, local import keeps module header clean
    main()
