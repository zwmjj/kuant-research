# 11 · Cross-Market Robustness: US vs CN

**Category:** Cross-Market
**Data tier:** 🟡 B — yfinance + akshare, no credentials
**Runtime:** ~45 seconds (akshare first-fetch dominates)

---

## Research question

Do the same four signals behave the same way across two completely
different markets? Specifically:

1. Does the **sign** of each signal's Sharpe agree across US and CN?
   (A consistent positive = real, universal pattern. A sign flip =
   local artifact.)
2. What is the **correlation** between the US version and the CN
   version of the same signal? (Low correlation = genuinely
   diversifying cross-market allocation. High correlation = you'd be
   double-counting risk.)
3. Do the IS/OOS stability characteristics line up?

This is the most honest cross-market robustness test you can do
without institutional data: same methodology, same parameters, same
signal definitions, two independent universes.

## Method

1. Load the 10-ETF US universe (yfinance, monthly).
2. Load the 8-index CN universe (akshare, monthly).
3. On each universe independently, build `mom12 / mom1 / lowvol / mr5`.
4. Run the quintile L/S backtest with identical cost/penalty settings.
5. Compute full + IS/OOS Sharpe for every (market, signal) pair.
6. Compute the pairwise cross-market correlation of matching signal
   streams (e.g. `corr(US.mom12, CN.mom12)`).
7. Report a sign-agreement table: did the Sharpe sign match across
   markets for each signal?

## Reproduce

```bash
cd research/11_cross_market_robustness
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31)

### Sharpe by signal × market

| Signal   | US Sharpe | US IS | US OOS | CN Sharpe | CN IS | CN OOS | Sign agree? |
|----------|-----------|-------|--------|-----------|-------|--------|-------------|
| `mom12`  | −0.256    | +0.00 | −0.51  | **+0.359**  | +0.81 | −0.16  | ❌ flip       |
| `mom1`   | +0.260    | −0.14 | +0.59  | +0.503    | −0.09 | **+1.12**  | ✅ agree      |
| `lowvol` | −0.265    | +0.44 | −0.87  | −0.220    | −0.10 | −0.31  | ✅ agree (−) |
| `mr5`    | +0.368    | +0.33 | +0.41  | +0.493    | +0.29 | +0.67  | ✅ agree     |

### Cross-market correlation of same-signal streams

```
  US.mom12  x  CN.mom12  = -0.057
  US.mom1   x  CN.mom1   = +0.017
  US.lowvol x  CN.lowvol = +0.128
  US.mr5    x  CN.mr5    = -0.073
```

All four cross-market correlations are within ±0.13. **A US/CN
combined book at 1:1 weights would be essentially uncorrelated across
the two legs** — this is a genuine diversification axis for a global
cross-sectional quant book.

### What we learn

1. **`mr5` is the most robust signal in the entire research book.**
   Positive Sharpe in both markets, positive IS *and* positive OOS
   in both markets, and better in CN (+0.49) than US (+0.37). It's
   also the champion in:
   - Study 01 (best cost-robust Sharpe)
   - Study 03 (only signal with positive α)
   - Study 05 (member of the best 3-signal blend)
   - Study 08 (only signal with stable IS/OOS)
   Five independent checks, same winner.

2. **`mom1` generalizes cross-market.** Both US and CN have negative
   IS and strongly positive OOS. The consistency of the flip across
   markets rules out "random noise in a 60-month window" — there's a
   genuine post-2020 regime shift in short-term mean reversion that
   affects both markets. CN's OOS Sharpe of +1.12 is very high and
   suggests the A-share market is a more favorable environment for
   short-term MR strategies than US sector ETFs.

3. **`mom12` is the only sign-flip in the book.** −0.26 in US,
   +0.36 in CN. Both IS and OOS disagree between markets — US
   momentum went from flat to bad, CN momentum went from strong to
   bad. This is consistent with the well-known Chinese-retail
   momentum story: A-share markets have historically shown strong
   medium-term momentum because retail-heavy flow amplifies price
   trends. That premium is decaying (CN OOS is −0.16) but the IS
   footprint is still there, whereas US sector-ETF momentum never
   had the same foundation.

4. **`lowvol` loses in both markets.** −0.27 US, −0.22 CN. The
   low-vol factor doesn't work on small asset universes over
   2016-2025 regardless of which market you pick. This is a cleaner
   version of the negative finding from study 09.

5. **Same-signal cross-market correlations are essentially zero.**
   This is a strong positive for the diversification case: a
   long-only US × CN factor book would be close to uncorrelated at
   the monthly frequency.

### Implication for portfolio construction

> **Run `mr5` in both US and CN at equal weights.** The cross-
> correlation is −0.07 so the combined book's vol is ~71% of the
> single-market version, and the combined Sharpe is higher than
> either leg alone.

This is the only portfolio recommendation the entire research book
supports on both cross-market and IS/OOS grounds.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
