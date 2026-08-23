# 07 · Optimization Diminishing Returns

**Category:** Portfolio Construction
**Data tier:** 🟡 B — yfinance
**Runtime:** <15 seconds

---

## Research question

Once you have a handful of signal return streams, **does fancy
portfolio optimization actually beat 1/N?** In the academic literature
this is DeMiguel-Garlappi-Uppal (2009) territory — they showed that
across 14 datasets, 1/N outperformed mean-variance optimization.
Does that conclusion hold in a tiny 4-strategy universe with a short
24-month estimation window?

## Method

1. Build the four reference signals and run the quintile L/S backtest
   on each to get a 4-wide strategy return matrix.
2. Apply four portfolio-allocation methods to that matrix:

   - **`equal_weight`** — 1/N, rebalanced monthly. Baseline.
   - **`inverse_vol`** — weight ∝ 1/σ on a 24-month rolling window.
     Simple risk-parity variant.
   - **`minimum_variance`** — unconstrained GMV on a 24-month rolling
     covariance. `w = Σ⁻¹1 / (1'Σ⁻¹1)`.
   - **`max_sharpe`** — unconstrained Markowitz tangency: `w ∝ Σ⁻¹μ`,
     normalized to sum-1. Notoriously unstable; we run it anyway so
     the instability is visible in the output.

3. Compute full-sample Sharpe / CAGR / MDD for each method.
4. Report each method's Sharpe **minus the 1/N baseline**. This is the
   "diminishing returns" curve — how much does each step up in
   sophistication actually buy you?

## Reproduce

```bash
cd research/07_optimization_diminishing
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs → 4 signals)

| Method             | Sharpe  | CAGR    | MDD     | Sharpe − 1/N |
|--------------------|---------|---------|---------|---------------|
| `equal_weight`     | +0.020  | −0.23%  | −24.3%  | baseline      |
| `inverse_vol`      | −0.049  | −0.81%  | −23.2%  | −0.069        |
| `minimum_variance` | −0.203  | −2.70%  | −32.5%  | −0.223        |
| `max_sharpe`       | **+0.253** 🚨 | **−16.12%** | **−94.2%** | **+0.233** |

### `max_sharpe` is the trap

Read the table carefully: `max_sharpe` has the **highest Sharpe** and
the **worst CAGR and MDD by a wide margin**. How is that possible?

It's **volatility drag**. The unconstrained tangency portfolio takes
extreme leveraged positions (5x, 10x, even larger on individual legs)
whenever the 24-month rolling covariance estimate is ill-conditioned
— which is most of the time on a 4-wide panel. The positive
arithmetic mean × low Sharpe-formula std produces a flattering Sharpe,
but the actual capital path is destroyed by the
`E[log R] ≈ E[R] − σ²/2` gap.

A −94% max drawdown on a strategy with a positive Sharpe ratio is the
classic DeMiguel-Garlappi-Uppal finding, reproduced here at small
scale. Do not trust the Sharpe column in isolation. **Always pair it
with the CAGR column and the drawdown column**, and always report all
three in any allocation comparison.

### The 1/N baseline is close to the frontier

On the three metrics that actually matter to a PM — risk-adjusted
return (Sharpe), geometric return (CAGR), and drawdown — the humble
`equal_weight` book is:

- The only method with a positive Sharpe, and the least negative CAGR of the four — note that all four CAGRs are negative over this window
- Tied with `inverse_vol` on drawdown
- 1000+ basis points ahead of `max_sharpe` on CAGR
- 70 percentage points ahead of `max_sharpe` on MDD

The "sophisticated" methods all underperform it on the full-risk
picture.

### What this means for portfolio construction

> **When your signal count × estimation window is small (4 × 24 here),
> allocation optimization is negative value-add.** The cost of
> estimation error on Σ⁻¹ and μ dominates any theoretical benefit.

The rule of thumb from the literature: you need about **250 × N**
observations to beat 1/N reliably with a mean-variance optimizer
(DeMiguel et al. 2009). With 4 strategies and 120 months, we're
well under that threshold — and the empirical result matches the
theory.

### Note on `inverse_vol` losing to 1/N

`inverse_vol` at −0.05 Sharpe (vs +0.02 for 1/N) is the surprise.
In principle inverse-vol weighting should be *at worst* tied with 1/N
because it's just a mild rescaling. The −0.07 gap comes from a
known problem: when one signal has spuriously low trailing vol in a
particular window, inverse-vol overweights it exactly when it's about
to mean-revert to a normal vol level — you're loading up on
assets that are quiet *because* they're about to be loud. In a longer
sample this effect averages out, but in 120 months it shows up.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
