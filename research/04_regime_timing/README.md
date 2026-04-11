# 04 · Regime Timing: Does VIX-Based Scaling Help?

**Category:** Portfolio Construction
**Data tier:** 🟢 A — yfinance only
**Runtime:** <20 seconds

---

## Research question

Take a working signal (`mom12` or `mr5`) and **scale its exposure by
the current VIX regime**. Does the regime overlay improve risk-
adjusted returns, or does it just chop the strategy in half at the
wrong times?

Five scaling rules:

| Rule             | Low-VIX | High-VIX | Intuition                          |
|------------------|---------|----------|------------------------------------|
| `full`           | 1.0     | 1.0      | baseline — no regime timing        |
| `risk_off_only`  | 0.0     | 1.0      | only run when VIX says risk-off    |
| `risk_on_only`   | 1.0     | 0.0      | only run when VIX says risk-on     |
| `scaled`         | 1.5     | 0.5      | contrarian — Barroso-Santa-Clara    |
| `anti_scaled`    | 0.5     | 1.5      | defensive — load when panicked      |

The `scaled` rule is the interesting one: it implements the momentum-
crash insurance idea from Barroso-Santa-Clara (2015) — lever up in
calm markets, de-risk in turbulence.

## Method

1. Build `mom12` and `mr5` signals on sector ETFs, run the quintile
   L/S backtest to get a monthly return stream per signal.
2. Fetch `^VIX` daily close from yfinance, resample to month-end,
   smooth with a 12-month moving average.
3. Classify each month as `high` or `low` using the expanding
   median of the smoothed VIX as the threshold (online, no lookahead).
4. For each signal × rule, scale the raw return stream by the
   rule's factor that month and recompute metrics.
5. Report Sharpe / CAGR / MDD and the delta vs the unconditional
   `full` baseline.

## Reproduce

```bash
cd research/04_regime_timing
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs)

### Full grid

| Signal  | Rule             | Sharpe     | CAGR     | MDD     | Δ vs `full` |
|---------|------------------|------------|----------|---------|-------------|
| `mom12` | `full`           | −0.256     | −2.54%   | −33.8%  | baseline    |
| `mom12` | `risk_off_only`  | −0.202     | −4.47%   | −42.2%  | +0.053      |
| `mom12` | `risk_on_only`   | −0.115     | −0.84%   | −19.6%  | +0.141      |
| `mom12` | `scaled`         | −0.221     | −3.30%   | −40.3%  | +0.034      |
| `mom12` | `anti_scaled`    | −0.215     | −7.94%   | −61.2%  | +0.041      |
| `mr5`   | `full`           | +0.368     | +4.34%   | −25.8%  | baseline    |
| `mr5`   | `risk_off_only`  | +0.082     | +0.20%   | −25.8%  | **−0.286**  |
| `mr5`   | `risk_on_only`   | **+0.692** | +3.30%   | **−4.8%** | **+0.324** |
| `mr5`   | `scaled`         | +0.569     | +5.24%   | −13.0%  | +0.202      |
| `mr5`   | `anti_scaled`    | +0.166     | +1.28%   | −38.1%  | −0.202      |

### The `mr5` × `risk_on_only` result is remarkable

Running `mr5` **only in low-VIX months** and sitting flat in high-VIX
months **almost doubles its Sharpe** (0.37 → 0.69) and **cuts its
max drawdown by 80%** (−25.8% → −4.8%). This is the single best
risk-adjusted improvement in the entire research book.

Why it works: `mr5` is a cross-sectional mean-reversion signal. In
high-VIX / risk-off regimes, single-name and single-sector variance
blows up, the cross-sectional ranking noise dominates the mean-
reversion signal, and the strategy loses money on random flips. In
low-VIX regimes the ranking is stable enough for the 5-month reversion
to play out cleanly.

`scaled` (Barroso-Santa-Clara style) is the second-best rule for
`mr5` at Sharpe 0.57, CAGR +5.24%, MDD −13%. It captures most of the
risk-on-only benefit while still earning something in high-VIX
months, so the total CAGR is higher (+5.24% vs +3.30%) even though
the Sharpe is slightly lower. If you care about total return more
than risk-adjusted return, `scaled` is the better pick.

### `mom12` can't be fixed by regime timing

Every variant of `mom12` is still negative. The best (`risk_on_only`
at −0.11) is less bad than the baseline (−0.26) but still a
money-loser. **Regime timing cannot rescue a signal that isn't
fundamentally there.** This is an important corollary to the `mr5`
result: the win is only possible because `mr5` had a genuine edge
to preserve. Applying the same regime overlay to a broken signal
just gives you a less-broken broken signal.

### Implications

> **Regime timing works as an *amplifier* of an existing edge, not as
> a rescue mechanism for a bad signal.** If your raw Sharpe is
> negative, no amount of regime cleverness will make it positive.
> If your raw Sharpe is mildly positive, a well-chosen regime rule
> can almost double it.

The practical recipe from this study: **run `mr5` + `risk_on_only`**
as the Kuant book's core single-factor strategy on ETF universes.
The Sharpe of 0.69 is the highest single-strategy number in the
whole research book, and it comes from a single public-data study
anyone can reproduce.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
