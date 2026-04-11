# 09 · Equity Vol Factors

**Category:** Factor Research / Risk
**Data tier:** 🟡 B — yfinance daily, no WRDS
**Runtime:** ~30 seconds

---

## Research question

Do the classic **volatility-based factors** work in a broad ETF
universe over 2016-2025? Specifically:

- **Realized volatility** (low-vol premium) — Haugen & Heins 1975,
  Frazzini-Pedersen BAB 2014
- **Downside vol** (semi-deviation) — a refinement that penalizes
  only bad-tail risk
- **Vol of vol** — higher-moment risk premium
- **Beta** (BAB / low-beta) — Fama-MacBeth forever, Frazzini-Pedersen 2014
- **Skewness** — Bali et al. 2011 lottery-premium (negative in their
  single-stock universe; we test whether the cross-asset ETF
  version reverses)

## Method

1. Pull daily returns for 20 ETFs (10 sectors + 4 broad equity + 3
   fixed income + 3 commodity) from yfinance.
2. For each factor, compute the raw estimate on rolling 12-month
   (252-day) windows daily, then take the last daily value per month
   as the monthly signal.
3. Shift the signal by one period so the signal at month-end t only
   uses info available through t (no lookahead).
4. Run the quintile L/S backtest with baseline cost config, 25% wide
   sleeves (5/5 ETFs on each side).
5. Report full-sample and 2020-split IS/OOS Sharpe per factor.

## Reproduce

```bash
cd research/09_equity_vol_factors
pip install -r requirements.txt
python run.py
```

First run downloads ~10 years of daily data for 20 ETFs via yfinance
— budget ~30 seconds. Subsequent runs are offline from the pickle
cache.

## Key findings (reference run, 2016-01-04 → 2025-12-31, 20-ETF universe)

| Factor         | Full Sharpe | IS Sharpe | OOS Sharpe | MDD    |
|----------------|-------------|-----------|------------|--------|
| `rvol_12m`     | −0.385      | +0.195    | **−1.087** | −65.3% |
| `downvol_12m`  | −0.469      | +0.089    | **−1.221** | −69.1% |
| `volofvol`     | −0.368      | +0.143    | −0.964     | −57.9% |
| `beta_spy`     | −0.556      | −0.242    | −0.903     | −67.9% |
| `skew`         | −0.666      | −1.094    | −0.209     | −64.2% |

### The headline: **every vol-based factor lost money in this universe**

All five factors have negative full-sample Sharpes, ranging from −0.37
to −0.67. Four of five have a positive-to-strongly-negative IS/OOS
flip. The drawdowns are all in the −58% to −69% range.

### Why this happened

The universe is the key. In a **cross-asset** ETF book (equities +
fixed income + commodities), the dominant cross-sectional variation
isn't low-vol-within-equities — it's **equity-vs-fixed-income**
directional risk premium. Over 2016-2025:

- **TLT, LQD, HYG** (fixed income) were low-vol, low-beta,
  low-downvol. They went LONG in every vol factor. They earned ~1-2%
  total return over the 10-year window.
- **QQQ, XLK, SPY** (growth equity) were high-vol, high-beta, high
  downvol. They went SHORT in every vol factor. They compounded
  ~300%+ over the same window.

The L/S book was long fixed income and short tech throughout the
biggest tech rally in history. The result is the unanimous negative
Sharpe across every factor formulation.

### What this study is *not* saying

It is **not** saying the low-vol premium is dead at the single-stock
level. Within an equity-only universe (e.g. S&P 500 constituents
from the WRDS backend in study 01), low-vol Sharpe is positive and
modest over the same period. The finding here is specific to the
cross-asset ETF universe: **in a universe where systematic
equity-vs-debt risk dominates, idiosyncratic vol factors all pick
up the wrong cross-section.**

### When to use this finding

- **Do not run vol factors cross-asset.** The dominant risk
  contribution is directional, and the factor ends up loading on
  that direction.
- **Always segment by asset class first**, then run within-segment
  vol factors. This study would look very different if we ran
  `rvol_12m` separately within equities and within fixed income.
  That's a natural next study — the scaffolding is all here.

### IS/OOS flip for skew is particularly striking

`skew`'s IS Sharpe was −1.09 (strongly negative) and its OOS Sharpe
is −0.21 (mildly negative). The skew premium *became less negative*
post-2020, which is the opposite of the decay trajectory the other
four factors show. Possibly related to regime shifts in equity kurtosis
distributions post-COVID — a finding worth revisiting once a longer
post-2020 sample is available.

## Files

```
README.md / run.py / config.yaml / signals.py / data.py /
requirements.txt / data_contract.md / expected_output.json
```
