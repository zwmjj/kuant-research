# 12 · Industry Rotation via Ken French Data

**Category:** Sector / Cross-Sectional Momentum
**Data tier:** 🟢 A — fully public, no credentials needed
**Runtime:** ~30 seconds after first cache build

---

## Research question

If you could buy the three best-performing U.S. industries from the last
twelve months and short the three worst, and rebalance once a month, would
you actually make money? How does that strategy's Sharpe evolve through
dot-com, GFC, QE, COVID, and post-2022 hiking regimes?

## Method

1. Pull the Kenneth French 10-industry monthly return series (1926–current).
2. At the end of every month, rank industries by trailing 12-month return.
3. Go equal-weight long the top 3, equal-weight short the bottom 3.
4. Compute full-sample and rolling 3-year Sharpe, and an in-sample vs.
   out-of-sample split at 2020-12-31.
5. Alongside the industry strategy, report the raw 10-decile momentum
   spread (Hi − Lo), and the operating-profitability / investment premia
   from Ken French's portfolio sorts as cross-checks on the underlying
   risk premia.

No WRDS. No Compustat. Everything in this study runs off the public
Dartmouth data library, so the results are literally reproducible by any
reader with a network connection.

## How to reproduce

```bash
# From the repo root:
cd research/12_industry_rotation
pip install -r requirements.txt
python run.py
```

`run.py` writes two artifacts:

- `sample_output/results.json` — the full numeric output
- `sample_output/summary.txt`  — a human-readable version of the key metrics

Compare your output against `expected_output.json` in this folder; the
numbers should match to 4 decimal places (the seed is deterministic and the
Ken French series are versioned).

## Parameters

Edit `config.yaml` to sweep:

- `start_date` / `end_date`       — sample period
- `lookback_months`               — momentum lookback (default 12)
- `top_n` / `bottom_n`            — number of industries on each side
- `industry_universe`             — 5, 10, 12, 17, 30, 38, 48, or 49
- `is_oos_split`                  — pivot date for IS/OOS decomposition
- `rolling_windows`               — list of (start, end, label) tuples

## Key findings (reference run, 2000-01-31 → 2025-12-31, 10-industry universe, 300 months)

| Metric             | Industry momentum L/S | Decile spread (Hi − Lo) | OP premium | INV premium |
|--------------------|-----------------------|-------------------------|------------|-------------|
| Full-sample Sharpe | **0.236**             | 0.138                   | 0.473      | 0.233       |
| CAGR               | 2.51%                 | −1.14%                  | —          | —           |
| Max drawdown       | −36.4%                | —                       | —          | —           |
| IS Sharpe (≤2020)  | 0.237                 | —                       | —          | —           |
| OOS Sharpe (>2020) | 0.236                 | —                       | —          | —           |

**Rolling 3-year Sharpe** for the industry L/S is all over the place —
negative in 03-05, 09-11, 15-17 and strongly positive in 06-08, 18-20. The
full-sample 0.23 is a volume-weighted average of a regime-dependent
premium, not a stable alpha.

**What we learn:**
1. **Industry-level momentum is weak and regime-dependent**, not the clean
   Jegadeesh-Titman premium you get at the single-stock level. The 3×3
   book averages over ~70% of the market, so most idiosyncratic alpha is
   diversified away.
2. **The IS/OOS split is remarkably stable** (0.237 vs 0.236) — unusual
   in factor research, and worth flagging: most momentum strategies
   degrade post-2020. The industry-level version survives because its
   premium is already so diluted there's not much further to fall.
3. **Operating profitability (OP Hi−Lo) is the strongest factor here
   at Sharpe 0.47** — a useful reminder that profitability has held up
   better than momentum across the full French data library.
4. **The decile Hi−Lo spread Sharpe of 0.14 is below the industry L/S**
   (0.24), which is counterintuitive — the decile spread is a much
   narrower book and should carry higher gross alpha. That it doesn't is
   consistent with momentum's post-2000 decay as the low-level anomaly
   most exposed to crash risk.

## Files

```
README.md             — this file
run.py                — entry point
config.yaml           — tunable parameters
signals.py            — ranking + long-short construction
requirements.txt      — minimal deps
data_contract.md      — input schema
expected_output.json  — reference results (reproducibility gate)
sample_output/        — regenerated on each run
```

## Source and license

Data:    Kenneth R. French Data Library, Tuck School of Business,
         Dartmouth College — public domain.
