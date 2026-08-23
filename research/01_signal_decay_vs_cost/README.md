# 01 · Signal Decay vs Transaction Cost

**Category:** Execution / Trade-cost Analysis
**Data tier:** 🟡 A/B — public yfinance by default, WRDS CRSP hook available
**Runtime:** ~30 seconds (first run downloads ETF history from yfinance)

---

## Research question

Every alpha signal has a turnover-cost trade-off. Rebalancing aggressively
captures the raw signal but pays cost; rebalancing lazily loses signal but
saves cost. **What does the full cost/Sharpe frontier look like, and where
does each signal's Sharpe peak?**

This is the foundational execution-research question for any systematic
book: it tells you the *cost budget* each strategy can tolerate before it
stops being a strategy.

## Method

We answer the question on a **10-sector-ETF universe** (XLK/XLF/XLE/XLV/
XLY/XLP/XLI/XLB/XLU/XLRE) instead of the full CRSP universe. Two reasons:

1. It's fully reproducible without WRDS. Anyone with `yfinance` can
   rerun it.
2. The *shape* of the cost/Sharpe trade-off is a property of the
   **signal**, not the universe — so the *slope* of Sharpe against cost
   is the object of interest here, not the absolute level, and a 10-ETF
   panel is enough to see a slope. Whether the same slope appears on a
   single-stock CRSP universe is a claim this study does not test.

A CRSP hook is included in `data.py` for anyone who wants to run the
single-stock version: point-in-time S&P 500 membership, the standard common-
stock screen, and Shumway (1997) delisting adjustment, reading
`WRDS_USERNAME` / `WRDS_PASSWORD` from the environment. **No result in this
repository comes from it** — a CRSP-backed figure is not checkable by a
reader without a subscription, so everything published here is the public
path. The delisting arithmetic is split out so it can be checked without a
WRDS session; the query itself ships unexercised. See `data_contract.md`.

### Signals (all price-based, no fundamentals needed)

| ID      | Formula                                            | Intuition          |
|---------|----------------------------------------------------|--------------------|
| `mom12` | trailing-12m return, 1m lag                        | Classic momentum   |
| `mom1`  | −(trailing-1m return), i.e. short-term reversal    | Mean-reversion     |
| `lowvol`| −(trailing-12m vol)                                | Low-volatility     |
| `mr5`   | −z-score of 5m return vs 12m mean                  | Medium-term MR     |

All four are computable from a return matrix alone. No WRDS / Compustat
access required.

### Experiment

For each signal:

1. Sweep `turnover_penalty ∈ [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30,
   0.40, 0.50, 0.60, 0.80, 1.00]`. Higher = lazier rebalancing.
2. At each penalty, run the quintile L/S backtest from `_core` and record
   Sharpe / CAGR / MDD.
3. Report the penalty that maximizes Sharpe per signal — this is the
   signal's **optimal cost budget point**.
4. Separately, sweep a `cost_multiplier ∈ {0.5, 1.0, 1.5, 2.0, 3.0, 5.0}`
   on the baseline commission+spread+impact config, holding penalty at
   its baseline (0.25). This measures **cost-sensitivity** — how does
   the signal degrade under harsher execution environments?
5. Compute signal **autocorrelation at lags 1..12** to estimate a
   "half-life" proxy. High autocorrelation = persistent signal = can
   tolerate heavier turnover penalty.

## How to reproduce

```bash
cd research/01_signal_decay_vs_cost
pip install -r requirements.txt
python run.py                 # yfinance fallback (default)
python run.py --source wrds   # point-in-time S&P 500, needs WRDS creds
```

Cache lives in `research/data_cache/` and is reused after first download.

## Parameters

`config.yaml`:

- `universe`           — list of tickers (default: 10 sector ETFs)
- `start_date`/`end_date`
- `signals`            — which signals to run (subset of {mom12, mom1, lowvol, mr5})
- `penalty_grid`       — list of turnover penalties to sweep
- `cost_multipliers`   — list of cost multipliers for the stress sweep
- `baseline_cost`      — commission/spread/impact baseline

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs, 120 months)

| Signal   | Best penalty | Best Sharpe | ACF@1  | Half-life | Sharpe @ 1× cost | Sharpe @ 5× cost |
|----------|--------------|-------------|--------|-----------|------------------|------------------|
| `mom12`  | **1.00**     | +0.233      | +0.805 | 4 mo      | −0.256           | −0.320           |
| `mom1`   | 0.05         | **+0.476**  | −0.204 | 1 mo      | +0.260           | +0.004           |
| `lowvol` | 1.00         | −0.229      | +0.962 | 9 mo      | −0.265           | −0.312           |
| `mr5`    | 0.30         | +0.471      | +0.621 | 2 mo      | +0.368           | **+0.226**       |

### Reading the table

1. **`mom12`'s optimal penalty is 1.0 (frozen).** In the 10-ETF
   universe with 120 months, sector-level momentum is so persistent
   (ACF@1 = 0.81) that *any* rebalancing destroys value. The best
   implementation is to pick the ranking once and hold it. This is a
   surprising but real finding of the small-universe run and reinforces
   the core point: signal persistence dominates cost.

2. **`mom1` is the opposite story.** Reversal signal, ACF@1 = −0.20,
   half-life 1 month. Best Sharpe at penalty 0.05 (the most aggressive
   rebalance). Cost sensitivity is the worst of the four — Sharpe goes
   from +0.48 → +0.26 → +0.00 as cost multiplies from 0.5× → 1× → 5×.
   Under realistic execution (1×+), this signal is marginally
   profitable; under bad execution (5×) it is **not** a strategy.

3. **`lowvol` has a negative Sharpe** across the whole penalty grid.
   In 10 sector ETFs over 2016–2025 the "low-vol premium" does not
   exist — utilities and staples underperformed high-vol tech over the
   window. This is an honest negative result: the study does **not**
   paper over it.

4. **`mr5` is the best cost-robust signal.** Best Sharpe 0.47 at
   penalty 0.30, and it's the only signal that still has Sharpe > 0.20
   at 5× baseline cost. Medium-term reversion (ACF@1 = 0.62, half-life
   2 months) hits the sweet spot: persistent enough to tolerate moderate
   turnover costs, fresh enough to generate real alpha.

### What this means for portfolio construction

> **A strategy's maximum tolerable cost level is not a fixed property —
> it's a function of how persistent the underlying signal is.**

Pair slow, high-persistence signals (like `mom12` or `lowvol`) with
lazy-rebalance or buy-and-hold implementations; the cost sensitivity is
dominated by the rebalance *decision*, not the cost per trade. Pair
fast signals (`mom1`) with the lightest-possible execution stack, or
drop them entirely under realistic cost assumptions.

### A word on the 10-ETF universe

Some of the numbers above will look different on CRSP. In particular:

- The full-CRSP `mom12` best penalty is typically 0.20–0.30 (not 1.0),
  because single-stock momentum is far less persistent than
  sector-level momentum.
- The lowvol premium typically appears when you broaden the universe
  beyond 10 sector ETFs — XLP and XLU aren't enough variation to see
  it on a 10-name book.

If you have WRDS credentials, `python run.py --source wrds` is where to
test both points on a single-stock universe. Expect to adapt the query —
it is a starting point, not a path this repository has exercised.

## Files

```
README.md
run.py                — entry point
config.yaml           — parameters
signals.py            — the 4 signal generators
data.py               — yfinance loader + optional WRDS hook
requirements.txt
data_contract.md
expected_output.json
sample_output/
```
