"""Unit tests for the shared core.

Every test constructs its own input and asserts against a value derived by
hand, so the suite runs offline and does not depend on any data source.

    python -m pytest research/_core/test_core.py -q
    python research/_core/test_core.py          # runs without pytest too
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research._core.backtest import _shrink_signal
from research._core.metrics import compute_metrics
from research._core.stats import ff5_regression


def _months(n, start="2020-01-31"):
    return pd.date_range(start, periods=n, freq="ME")


# --------------------------------------------------------------------------
# metrics: downside deviation is measured about the target, not about the
# mean of the negative returns
# --------------------------------------------------------------------------
def test_sortino_uses_shortfall_about_zero():
    idx = _months(4)
    rets = pd.Series([0.10, -0.02, 0.10, -0.08], index=idx)
    m = compute_metrics(rets, periods_per_year=12)

    shortfall = np.array([0.0, -0.02, 0.0, -0.08])
    downside = np.sqrt((shortfall ** 2).mean()) * np.sqrt(12)
    expected = rets.mean() * 12 / downside
    assert abs(m["sortino"] - round(float(expected), 4)) < 1e-4

    # The shortcut this replaced — std of the losing periods about their own
    # mean — is a different statistic, and it lands on either side depending
    # on how frequent and how dispersed the losses are. Both directions are
    # exercised below so nobody "simplifies" this back by accident.
    def shortcut(x):
        neg = x[x < 0]
        return float(neg.std() * np.sqrt(12)) if len(neg) > 1 else np.nan

    def target_semidev(x):
        return float(np.sqrt((np.minimum(x.values, 0.0) ** 2).mean()) * np.sqrt(12))

    rare_losses = pd.Series([0.05] * 10 + [-0.02, -0.08], index=_months(12))
    frequent_losses = pd.Series([0.01, -0.03] * 6, index=_months(12))
    assert shortcut(rare_losses) > target_semidev(rare_losses)
    assert shortcut(frequent_losses) < target_semidev(frequent_losses)


def test_sortino_zero_when_no_losing_period():
    idx = _months(3)
    m = compute_metrics(pd.Series([0.01, 0.02, 0.03], index=idx), periods_per_year=12)
    assert m["sortino"] == 0.0          # no shortfall -> undefined, reported as 0
    assert m["max_drawdown"] == 0.0


def test_sharpe_is_return_over_vol_when_no_rf_given():
    idx = _months(24)
    rng = np.random.default_rng(0)
    rets = pd.Series(rng.normal(0.01, 0.03, 24), index=idx)
    m = compute_metrics(rets, periods_per_year=12)
    assert abs(m["sharpe"] - round(float(rets.mean() / rets.std() * np.sqrt(12)), 4)) < 1e-9


def test_sharpe_drops_when_rf_is_supplied():
    idx = _months(24)
    rng = np.random.default_rng(1)
    rets = pd.Series(rng.normal(0.01, 0.02, 24), index=idx)
    rf = pd.Series(0.003, index=idx)
    assert compute_metrics(rets, 12, rf=rf)["sharpe"] < compute_metrics(rets, 12)["sharpe"]


# --------------------------------------------------------------------------
# backtest: freezing a signal must not import an asset's future
# --------------------------------------------------------------------------
def test_frozen_signal_has_no_lookahead():
    idx = _months(4)
    sig = pd.DataFrame({
        "A": [1.0, 2.0, 3.0, 4.0],       # present throughout
        "B": [np.nan, np.nan, 9.0, 8.0],  # only exists from period 3
    }, index=idx)
    frozen = _shrink_signal(sig, penalty=1.0)

    assert list(frozen["A"]) == [1.0, 1.0, 1.0, 1.0]       # first observed value, held
    assert frozen["B"].iloc[:2].isna().all()               # absent before it existed
    assert list(frozen["B"].iloc[2:]) == [9.0, 9.0]        # first observed value, held

    # The old `signal.bfill().iloc[0]` would have put B's 9.0 into periods 1-2,
    # which is a value that did not exist yet at those dates.
    assert sig.bfill().iloc[0]["B"] == 9.0


def test_shrinkage_endpoints():
    idx = _months(3)
    sig = pd.DataFrame({"A": [1.0, 5.0, 9.0]}, index=idx)
    assert _shrink_signal(sig, 0.0).equals(sig)                 # penalty 0 -> untouched
    assert list(_shrink_signal(sig, 1.0)["A"]) == [1.0, 1.0, 1.0]
    partial = _shrink_signal(sig, 0.5)["A"]
    assert partial.iloc[0] == 1.0 and 1.0 < partial.iloc[1] < 5.0


# --------------------------------------------------------------------------
# stats: a dollar-neutral spread is self-financing, so no RF deduction
# --------------------------------------------------------------------------
def _ff5_panel(n=60, rf=0.004, seed=2):
    idx = _months(n, "2015-01-31")
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "Mkt-RF": rng.normal(0.006, 0.04, n),
        "SMB":    rng.normal(0.001, 0.02, n),
        "HML":    rng.normal(0.001, 0.02, n),
        "RMW":    rng.normal(0.001, 0.015, n),
        "CMA":    rng.normal(0.001, 0.015, n),
        "RF":     np.full(n, rf),
    }, index=idx)


def test_self_financing_spread_is_not_rf_adjusted():
    ff5 = _ff5_panel()
    rng = np.random.default_rng(3)
    spread = pd.Series(rng.normal(0.002, 0.02, len(ff5)), index=ff5.index)

    a_default = ff5_regression(spread, ff5)["alpha"]
    a_excess = ff5_regression(spread, ff5, self_financing=False)["alpha"]

    # Deducting a constant RF shifts the intercept down by exactly RF, annualised.
    assert abs((a_default - a_excess) - 0.004 * 12) < 1e-6
    assert ff5_regression(spread, ff5)["n"] == len(ff5)


def test_regression_recovers_a_planted_beta():
    ff5 = _ff5_panel(n=120, seed=4)
    y = 0.001 + 0.8 * ff5["Mkt-RF"] - 0.4 * ff5["SMB"]
    r = ff5_regression(y, ff5)
    assert abs(r["beta_mkt"] - 0.8) < 1e-3
    assert abs(r["beta_smb"] + 0.4) < 1e-3
    assert abs(r["alpha"] - 0.001 * 12) < 1e-6
    assert r["r2"] > 0.999


def test_regression_refuses_short_overlap():
    ff5 = _ff5_panel(n=12)
    out = ff5_regression(pd.Series(0.01, index=ff5.index), ff5)
    assert "error" in out


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except AssertionError as exc:
                fails += 1
                print(f"  FAIL  {name}  {exc}")
    print(f"\n{'all tests passed' if not fails else str(fails) + ' FAILED'}")
    raise SystemExit(1 if fails else 0)
