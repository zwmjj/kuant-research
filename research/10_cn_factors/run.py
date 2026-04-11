#!/usr/bin/env python
"""A-share factor proxies — entry point.

Reads config.yaml, pulls 8 A-share indices from akshare, constructs 5
long-short factor proxies, computes standard stats + IS/OOS + rolling
windows, adds a cross-market correlation vs. FF5 US market, and a US
vol-regime cross-analysis. Writes results.json and a summary.txt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from research._core import compute_metrics, split_is_oos, rolling_windows  # noqa: E402
from research._data import fetch_cn_indices, fetch_ff5  # noqa: E402
from signals import (  # noqa: E402
    build_all_factors,
    us_vol_regime,
    value_growth_cycle,
)


def main():
    with open(HERE / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    start = cfg["start_date"]
    end = cfg["end_date"]
    split_date = cfg["is_oos_split"]
    windows = [tuple(w) for w in cfg["rolling_windows"]]

    # ── data ───────────────────────────────────────────────
    print(f"[data] fetching {len(cfg['indices'])} A-share indices via akshare ...")
    panel = fetch_cn_indices(indices=cfg["indices"], start=start)
    panel = panel[(panel.index >= start) & (panel.index <= end)]
    print(f"[data] panel: {panel.shape[0]} months x {panel.shape[1]} indices "
          f"({list(panel.columns)})")

    results = {
        "config": {"start": start, "end": end, "split_date": split_date},
        "panel_coverage": {
            col: {
                "n_months": int(panel[col].notna().sum()),
                "first_obs": str(panel[col].first_valid_index().date()) if panel[col].notna().any() else None,
                "last_obs":  str(panel[col].last_valid_index().date())  if panel[col].notna().any() else None,
            }
            for col in panel.columns
        },
    }

    # ── factor proxies ─────────────────────────────────────
    print("[factors] building long-short proxies ...")
    factors = build_all_factors(panel, cfg["factors"])
    factor_stats = {}
    for name, series in factors.items():
        factor_stats[name] = {
            "overall": compute_metrics(series, periods_per_year=12),
            "is_oos":  split_is_oos(series, split_date=split_date, periods_per_year=12),
            "rolling": rolling_windows(series, windows, periods_per_year=12),
        }
        m = factor_stats[name]["overall"]
        print(f"  {name:10s}: Sharpe={m['sharpe']:+.3f}  CAGR={m['cagr']:+.2%}  "
              f"MDD={m['max_drawdown']:.2%}  n={m['n_periods']}")
    results["factor_proxies"] = factor_stats

    # ── cross-market correlation ───────────────────────────
    if cfg.get("us_regime"):
        print("[cross] fetching FF5 for US market return ...")
        try:
            ff5 = fetch_ff5(start=start, end=end)
            us_mkt = ff5["Mkt-RF"] + ff5["RF"]
            us_mkt = us_mkt[(us_mkt.index >= start) & (us_mkt.index <= end)]

            # Align all CN indices + US to month-end
            corr_panel = panel.copy()
            corr_panel["US_Market"] = us_mkt
            corr_panel = corr_panel.dropna()
            corr = corr_panel.corr()
            results["cross_correlation"] = {
                "labels": list(corr.columns),
                "values": [[round(float(corr.iloc[i, j]), 4) for j in range(len(corr))]
                           for i in range(len(corr))],
                "n_months": int(len(corr_panel)),
            }
            us_csi = float(corr.loc["US_Market", "CSI300"]) if "CSI300" in corr.columns else None
            print(f"[cross] US x CSI300 corr = {us_csi:+.3f}")

            # ── US vol regime cross-analysis ──────────────
            regime = us_vol_regime(us_mkt)
            regime_stats = []
            for cn_name in ["CSI300", "CSI500", "GEM", "LowVol"]:
                if cn_name not in panel.columns:
                    continue
                cn_r = panel[cn_name]
                aligned = pd.concat([cn_r, regime["regime"]], axis=1).dropna()
                for r_label in ["low", "high"]:
                    sub = aligned[aligned["regime"] == r_label].iloc[:, 0]
                    if len(sub) < 6 or sub.std() == 0:
                        continue
                    regime_stats.append({
                        "cn_index": cn_name,
                        "us_regime": r_label,
                        "sharpe": round(float(sub.mean() / sub.std() * np.sqrt(12)), 4),
                        "mean_ret": round(float(sub.mean()), 6),
                        "n_months": int(len(sub)),
                    })
            results["us_vol_cn_regime"] = regime_stats
        except Exception as e:
            print(f"[cross] skipped — {e}")
            results["cross_correlation"] = None
            results["us_vol_cn_regime"] = []

    # ── value/growth cycle ─────────────────────────────────
    if "HML_CN" in factors:
        cycle = value_growth_cycle(
            factors["HML_CN"],
            [tuple(w) for w in cfg["value_growth_cycle_windows"]],
        )
        results["value_growth_cycle"] = cycle
        print("\n[cycle] Value-Growth cycle:")
        for c in cycle:
            print(f"  {c['period']}: {c['cumulative_return']:+.2%} → {c['winner']} wins")

    # ── LowVol rolling ─────────────────────────────────────
    if "LowVol_CN" in factors:
        lv_rolling = rolling_windows(
            factors["LowVol_CN"],
            [tuple(w) for w in cfg["lowvol_rolling_windows"]],
            periods_per_year=12,
        )
        results["lowvol_rolling"] = lv_rolling

    # ── write outputs ──────────────────────────────────────
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
    lines = ["A-SHARE FACTOR PROXIES"]
    for name, fs in results.get("factor_proxies", {}).items():
        m = fs["overall"]
        iso = fs["is_oos"]
        lines.append(
            f"  {name:10s}  Sharpe={m['sharpe']:+.3f}  "
            f"IS={iso['is']['sharpe']:+.3f}  OOS={iso['oos']['sharpe']:+.3f}  "
            f"CAGR={m['cagr']:+.2%}  MDD={m['max_drawdown']:.2%}"
        )
    if results.get("cross_correlation"):
        cc = results["cross_correlation"]
        idx = cc["labels"].index("US_Market") if "US_Market" in cc["labels"] else None
        if idx is not None:
            lines.append("\nUS_Market correlations:")
            for lbl, row in zip(cc["labels"], cc["values"]):
                if lbl == "US_Market":
                    continue
                lines.append(f"  US x {lbl:10s} = {row[idx]:+.3f}")
    if results.get("value_growth_cycle"):
        lines.append("\nValue/Growth cycle:")
        for c in results["value_growth_cycle"]:
            lines.append(f"  {c['period']:10s}  cum={c['cumulative_return']:+.2%}  → {c['winner']}")
    return "\n".join(lines)


def _reproducibility_check(results):
    ref_path = HERE / "expected_output.json"
    if not ref_path.exists():
        print("\n[repro] no expected_output.json — first run, commit results.json as reference.")
        return
    with open(ref_path, encoding="utf-8") as f:
        ref = json.load(f)

    checked, failed = 0, []
    for name in results.get("factor_proxies", {}):
        if name not in ref.get("factor_proxies", {}):
            continue
        a = results["factor_proxies"][name]["overall"]
        b = ref["factor_proxies"][name]["overall"]
        for metric in ("sharpe", "cagr", "max_drawdown"):
            av, bv = a.get(metric), b.get(metric)
            if av is None or bv is None:
                continue
            if abs(av - bv) > 1e-3:
                failed.append((name, metric, av, bv))
            checked += 1
    if failed:
        print(f"\n[repro] DRIFT — {len(failed)}/{checked} checks failed:")
        for name, metric, a, b in failed:
            print(f"  {name}.{metric}: got {a:.4f} expected {b:.4f}")
        sys.exit(1)
    print(f"\n[repro] OK — {checked} metrics match expected_output.json within 1e-3")


if __name__ == "__main__":
    main()
