"""Synthetic-universe generator + the usual 12-month momentum signal.

The key function here is `generate_universe_with_delisting`, which
builds two parallel return panels:

  `survivors_panel`  — only the assets that exist in month t get a
                       return, delisted assets vanish from the panel
                       with no record of their terminal drop. This is
                       what a survivorship-biased backtest sees.

  `full_panel`       — every asset has a return in every month,
                       including a terminal negative shock in the
                       month it "delists". This is what a delisting-
                       adjusted WRDS CRSP backtest sees.

Running the same factor on both panels and comparing Sharpes gives
you the survivorship-bias magnitude empirically.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_universe_with_delisting(
    n_assets: int,
    n_months: int,
    seed: int,
    delist_prob_per_month: float,
    delist_return_mean: float,
    delist_return_std: float,
    min_life_months: int,
):
    """Build two monthly return panels: survivors-only and full.

    Each asset:
      - Gets a latent "quality" score ~ N(0, 1) that sets its mean
        monthly return (higher quality = higher mean, so factors
        actually have something to rank on).
      - Has an individual vol drawn from U(0.04, 0.10).
      - Each month (after min_life_months), faces a `delist_prob_per_month`
        chance of receiving a delisting shock. If triggered, the asset
        is dead from that month onward.
      - If triggered, its final month's return is drawn from
        N(delist_return_mean, delist_return_std).

    Returns
    -------
    (survivors, full, delist_events)
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2005-01-31", periods=n_months, freq="ME")
    cols = [f"A{i:03d}" for i in range(n_assets)]

    # Draw quality and vol
    quality = rng.normal(0.0, 0.004, n_assets)   # monthly mean ≈ ±0.4%
    vol = rng.uniform(0.04, 0.10, n_assets)

    # Draw returns
    raw = rng.normal(
        loc=quality[np.newaxis, :],
        scale=vol[np.newaxis, :],
        size=(n_months, n_assets),
    )

    # Decide delisting events
    alive_until = np.full(n_assets, n_months, dtype=int)  # last alive index
    delist_events = []
    for i in range(n_assets):
        for t in range(min_life_months, n_months):
            if rng.random() < delist_prob_per_month:
                alive_until[i] = t
                # Draw terminal shock
                shock = rng.normal(delist_return_mean, delist_return_std)
                raw[t, i] = shock
                delist_events.append({
                    "asset": cols[i],
                    "month": int(t),
                    "date": dates[t].isoformat(),
                    "terminal_return": float(shock),
                })
                break

    # Full panel (what CRSP-with-delisting sees): raw, but NaN after alive_until.
    full = pd.DataFrame(raw, index=dates, columns=cols).copy()
    for i in range(n_assets):
        if alive_until[i] < n_months:
            full.iloc[alive_until[i] + 1:, i] = np.nan

    # Survivors panel (what a naive 'only keep names with full history' sees):
    # drop any column that has a delisting event at all.
    survivors = full.copy()
    delisted_cols = [e["asset"] for e in delist_events]
    survivors = survivors.drop(columns=delisted_cols)

    return survivors, full, delist_events


def signal_mom12(returns: pd.DataFrame) -> pd.DataFrame:
    cum = (1 + returns).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True)
    return cum.shift(1)
