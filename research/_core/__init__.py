"""Shared core used by every reproducible study in this folder.

Kept deliberately small — just the pieces needed to run a long/short
cross-sectional backtest on a returns matrix:

    metrics     — Sharpe / CAGR / MDD / IS-OOS decomposition
    backtest    — quintile long-short engine with turnover penalty
    costs       — simple proportional + sqrt-impact cost model
    data_loader — three data sources: cached pickle, yfinance, CSV

Everything here is intentionally standalone — no qf/ imports, so a user can
clone this repo, `pip install -r requirements.txt`, and run any study
without needing the wider Kuant platform.
"""

from research._core.metrics import compute_metrics, split_is_oos, rolling_windows
from research._core.costs import apply_turnover_cost, CostConfig
from research._core.backtest import long_short_quintile_backtest
from research._core.data_loader import load_returns_panel
from research._core.stats import (
    ff5_regression,
    correlation_matrix,
    rolling_vol,
    blend_factors,
)

__all__ = [
    "compute_metrics",
    "split_is_oos",
    "rolling_windows",
    "apply_turnover_cost",
    "CostConfig",
    "long_short_quintile_backtest",
    "load_returns_panel",
    "ff5_regression",
    "correlation_matrix",
    "rolling_vol",
    "blend_factors",
]
