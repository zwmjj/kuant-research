# 13 · New Factors with FRED Macro Conditioners

**Category:** Factor Research / Macro
**Data tier:** 🟡 B — yfinance + FRED, no credentials
**Runtime:** ~20 seconds

---

## Research question

Does adding a **macroeconomic regime layer** on top of price-based
signals improve or hurt performance? Specifically: can we take a
price-based factor (momentum, low-vol) and tilt it based on the
current VIX / yield curve / macro regime, and get a better result
than the raw version?

## Method

Three signals, all of which combine a price-based base with a
macro-derived conditioner:

- **`vix_regime`** — base = low-vol factor (−12m rolling std). Multiplier:
  +1 when VIX is above its 12-month expanding median (risk-off regime),
  −1 when below. Intuition: low-vol pays in risk-off, hurts in risk-on.
- **`curve_signal`** — base = 6-month asset momentum. Multiplier: sign of
  3-month change in T10Y2Y (yield curve slope). Steepening curve →
  long cyclicals, flattening → short cyclicals.
- **`macro_blend`** — base = 12-month momentum. Tilt = average
  z-score of (−VIX, −DGS10, +T10Y2Y, −UNRATE) → a single "risk-on"
  score. Risk-on amplifies, risk-off dampens the momentum signal.

Each signal is run through the standard quintile L/S backtest with
the baseline cost config, 25% sleeves.

## Reproduce

```bash
cd research/13_new_factors
pip install -r requirements.txt
python run.py
```

First run pulls daily FRED series over 2015-2025 (~50 KB) and caches
them. All subsequent runs are offline.

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs + FRED macros)

| Signal          | Full Sharpe | IS Sharpe | OOS Sharpe | MDD    |
|-----------------|-------------|-----------|------------|--------|
| `vix_regime`    | −0.218      | +0.094    | −0.480     | −53.1% |
| `curve_signal`  | **+0.175**  | **+0.656**| −0.234     | −36.9% |
| `macro_blend`   | −0.291      | −0.021    | −0.542     | −51.5% |

### What we learn

1. **`curve_signal` is the most interesting result** — positive full-
   sample Sharpe of +0.18 with a very strong IS Sharpe of +0.66 and
   a sharply negative OOS of −0.23. Classic overfitting signature:
   the signal worked pre-2020 (when the curve moves cleanly led
   cyclical rotation) and broke post-2020 (when the yield curve spent
   extended periods inverted without the usual recession follow-
   through). This is the cleanest IS→OOS decay in the whole research
   book.

2. **`vix_regime` is weakly negative** — the VIX-conditioner didn't
   rescue the low-vol factor in the 10-ETF universe (where we already
   saw from study 09 that low-vol is broken for cross-asset flows).
   IS +0.09 to OOS −0.48 is a similar overfitting story at half the
   magnitude.

3. **`macro_blend` is the worst of the three** — even the IS Sharpe
   is essentially zero. A kitchen-sink macro conditioner that averages
   VIX/yields/curve/unemployment doesn't produce a coherent regime
   signal on this sample. Too many noisy components averaged together
   give you... more noise.

### The uncomfortable conclusion

> **Macro conditioners are overfitting amplifiers on small samples.**
> Every signal in this study that looked good IS (`curve_signal`,
> `vix_regime` pre-split) broke post-2020, with much steeper OOS
> decay than any of the pure price-based signals in studies 01 / 08.

The mechanism is degrees of freedom: a macro conditioner asks which
regime definition, which conditioner form, and which lookback, and each
choice is another opportunity to fit the sample. A clean price-based signal with
no discretionary regime overlay is a harder target to overfit.

### What would make this study produce better results

- **Longer history.** 2000-2025 (via WRDS CRSP backend) instead of
  2015-2025 gives the macro conditioner ~3x more regime observations.
- **Wider universe.** 500+ US single stocks instead of 10 sector ETFs
  creates more cross-sectional signal for the macro tilt to
  differentiate.
- **Smaller degrees of freedom.** One conditioner at a time, not four.

The ETF-only version is the one shipped here, because it is the one a
reader can run. The three changes above would make the test more
informative; none of them has been run, so nothing in this study should be
read as evidence about what a wider, longer-history version would show.

## Files

```
README.md / run.py / config.yaml / signals.py / data.py /
requirements.txt / data_contract.md / expected_output.json
```
