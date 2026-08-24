# 03 · Factor Crowding: R², Alpha, and Exposures

**Category:** Factor Research
**Data tier:** 🟡 B — yfinance + Ken French, no WRDS required
**Runtime:** <20 seconds

---

## Research question

When we look at a strategy's return stream, **how much of its Sharpe is
alpha** (residual after netting out the Fama-French 5 factors) and how
much is just compensated exposure to known risk premia?

A "crowded" factor is one whose return is mostly explained by
Market/SMB/HML/RMW/CMA — its Sharpe isn't alpha, it's smart-beta. A
factor with high α and low R² is an actual edge. This study runs the
same four reference signals from `01_signal_decay_vs_cost` through an
FF5 regression and reports:

- Annualized α and its t-statistic
- Each of the five betas
- Regression R²
- The correlation matrix between the four strategies (independent
  crowding check — if two "different" signals are 0.8-correlated, one
  is a rediscovery of the other).

## Method

1. Build the four signals on 10 sector ETFs, same as study 01.
2. Run the quintile L/S backtest to get a monthly return stream per
   signal.
3. For each stream, OLS regress `excess_return = α + Σ β_i * factor_i`
   on the FF5 monthly panel.
4. Report α, α-t, all five betas, and R² — all computed in pure numpy
   (no `statsmodels` dependency) to keep the install minimal.
5. Compute the strategy × strategy correlation matrix.

## Reproduce

```bash
cd research/03_factor_crowding
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs)

### FF5 regression

| Signal   | Sharpe | α (ann) | α-t   | β_mkt  | β_smb  | β_hml  | β_rmw  | β_cma  | R²    |
|----------|--------|---------|-------|--------|--------|--------|--------|--------|-------|
| `mom12`  | −0.26  | −2.0%   | −0.39 | −0.12  | −0.43  | −0.25  | −0.43  | +0.68  | 0.20  |
| `mom1`   | +0.26  | +2.1%   | +0.39 | +0.22  | −0.02  | ±0.00  | −0.18  | +0.14  | 0.05  |
| `lowvol` | −0.27  | −1.8%   | −0.42 | −0.35  | −0.21  | −0.54  | +0.39  | +0.15  | **0.40** |
| `mr5`    | +0.37  | **+3.4%** | +0.72 | +0.16  | −0.04  | −0.19  | −0.05  | +0.36  | 0.04  |

### Strategy × strategy correlation

```
             mom12    mom1  lowvol    mr5
    mom12   +1.000  -0.216  +0.331  +0.007
    mom1    -0.216  +1.000  -0.083  +0.422
    lowvol  +0.331  -0.083  +1.000  +0.045
    mr5     +0.007  +0.422  +0.045  +1.000
```

### What we learn

1. **`mr5` has the largest alpha**, at +3.4% annualized — but with a
   t-stat of only +0.72, it is *not* statistically significant in this
   120-month sample. `mom1` is also positive (+2.1%, t = +0.39), so the
   sign alone does not separate them; neither can be cleanly distinguished
   from zero with ten years of monthly data on a 10-ETF universe.

   These alphas are roughly two percentage points higher than an earlier
   version of this study reported, and the reason is a correction, not a
   data revision: the regressand had the risk-free rate deducted from it.
   These signals are dollar-neutral long/short spreads — the long leg is
   funded by the short leg, no cash is tied up — so deducting the
   risk-free rate understated every alpha by the whole risk-free rate.
   At 2015-2025 levels that is about two points a year, which is larger
   than most of the alphas being measured.

2. **`lowvol` is the most FF5-explained of the four** — R² = 0.40, a
   big negative HML (−0.54) and RMW (+0.41) — basically a
   quality/anti-value tilt. Its negative α (−1.8%) means the
   low-vol premium in ETF sectors over 2015-2025 is **worse than pure
   smart-beta exposure**; you'd do better just holding the FF5 blend
   directly.

3. **`mom12` has R² = 0.19 and negative alpha.** The 10-ETF
   implementation of momentum is both partially FF5-replicable and
   earning a loss on the residual. This is the clearest "don't run
   this signal in this universe" result in the whole research book.

4. **None of the four strategies are dangerously crowded.** The highest
   absolute correlation is +0.42 (`mom1` × `mr5`) — both are
   mean-reversion signals at different horizons, so the correlation
   makes mechanical sense. The lowest is +0.007 (`mom12` × `mr5`):
   momentum and mean-reversion are truly independent axes, exactly
   as the theory says.

### The key distinction this study makes

> **Negative alpha after FF5 = "you were just paying to run a costly
> wrapper around a known risk premium."**
>
> **Positive alpha, high R² = "your signal is crowded but earns its
> keep against the factors it hugs."**
>
> **Positive alpha, low R² = "independent edge — assuming the t-stat
> holds up."**

Only `mr5` falls in the third bucket here, and even its t-stat is too
weak to bank on. This is the honest content of the study — a small-
universe run is *not* enough to claim factor edges, only to reject
obviously broken ones.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
