"""Small statistical helpers shared by Phase 2 studies.

Kept here (not in metrics.py) so it's clear what's a single-return-stream
metric versus a cross-series / regression helper.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


def ff5_regression(
    strategy_returns: pd.Series,
    ff5: pd.DataFrame,
    periods_per_year: int = 12,
    self_financing: bool = True,
) -> dict:
    """Regress a strategy's return on the FF5 factors.

    Parameters
    ----------
    strategy_returns : pd.Series
        Strategy monthly returns (decimal).
    ff5 : pd.DataFrame
        Ken French 5-factor panel. Expected columns: Mkt-RF, SMB, HML,
        RMW, CMA, RF. Decimal returns.
    self_financing : bool, default True
        True for a dollar-neutral long/short spread: the long leg is funded
        by the short leg, so the strategy never ties up cash and the
        risk-free rate must NOT be deducted. Deducting it understates alpha
        by the full risk-free rate — roughly 3-4%/yr at 2023-2025 levels,
        which is larger than most of the alphas being measured.
        Set False only for a long-only or otherwise cash-consuming book,
        where the regressand is genuinely an excess return.

    Returns
    -------
    dict with:
        alpha              — annualized intercept (decimal)
        alpha_t            — t-statistic of the intercept
        beta_mkt, beta_smb, beta_hml, beta_rmw, beta_cma
        r2                 — regression R²
        n                  — number of observations
    """
    cols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
    common = strategy_returns.index.intersection(ff5.index)
    if len(common) < 24:
        return {"error": "insufficient overlap (<24 months)", "n": int(len(common))}

    y = strategy_returns.loc[common]
    if not self_financing:
        y = y - ff5.loc[common, "RF"]
    X = ff5.loc[common, cols].copy()
    X.insert(0, "const", 1.0)

    # OLS via numpy lstsq — no statsmodels dependency.
    A = X.values
    b = y.values
    beta, *_ = np.linalg.lstsq(A, b, rcond=None)
    resid = b - A @ beta
    dof = len(b) - A.shape[1]
    sigma2 = (resid @ resid) / dof if dof > 0 else np.nan
    xtx_inv = np.linalg.pinv(A.T @ A)
    se = np.sqrt(np.diag(sigma2 * xtx_inv))
    t_stats = beta / se

    ss_res = float(resid @ resid)
    y_demean = b - b.mean()
    ss_tot = float(y_demean @ y_demean)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "alpha": round(float(beta[0] * periods_per_year), 6),
        "alpha_monthly": round(float(beta[0]), 6),
        "alpha_t": round(float(t_stats[0]), 4),
        "beta_mkt": round(float(beta[1]), 4),
        "beta_smb": round(float(beta[2]), 4),
        "beta_hml": round(float(beta[3]), 4),
        "beta_rmw": round(float(beta[4]), 4),
        "beta_cma": round(float(beta[5]), 4),
        "r2": round(float(r2), 4),
        "n": int(len(common)),
    }


def correlation_matrix(panel: pd.DataFrame) -> dict:
    """Return a JSON-friendly symmetric correlation matrix."""
    corr = panel.corr()
    return {
        "labels": list(corr.columns),
        "values": [[round(float(corr.iloc[i, j]), 4) for j in range(len(corr))]
                   for i in range(len(corr))],
    }


def rolling_vol(returns: pd.Series, window: int = 12, periods_per_year: int = 12) -> pd.Series:
    """Annualised rolling volatility."""
    return returns.rolling(window).std() * np.sqrt(periods_per_year)


def blend_factors(
    factor_returns: Dict[str, pd.Series],
    weights: Optional[Dict[str, float]] = None,
) -> pd.Series:
    """Linear blend of multiple factor return streams.

    If weights are None, equal-weights across factors. Aligns on the
    intersection of all factors' dates (no forward-fill).
    """
    if not factor_returns:
        return pd.Series(dtype=float)
    if weights is None:
        weights = {k: 1.0 / len(factor_returns) for k in factor_returns}
    df = pd.DataFrame(factor_returns).dropna(how="any")
    w = pd.Series(weights).reindex(df.columns).fillna(0)
    return (df * w).sum(axis=1).rename("blend")
