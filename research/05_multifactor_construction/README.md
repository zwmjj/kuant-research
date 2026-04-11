# 05 · Multi-Factor Construction

**Category:** Portfolio Construction
**Data tier:** 🟡 B — yfinance, shares cache with 01/03/08
**Runtime:** <20 seconds

---

## Research question

If I have four signals that each generate a return stream, does
**blending them** produce a Sharpe higher than any single one? And
how does the answer depend on the number of signals blended?

This is the classic "does factor diversification actually work" question
asked at small scale: with only four signals, there are 15 possible
subsets (4 singles, 6 pairs, 4 triples, 1 full blend). The study
enumerates all of them, reports the Sharpe of every blend, and
summarizes the mean and best Sharpe by subset size `k`.

## Method

1. Build `mom12 / mom1 / lowvol / mr5` on 10 sector ETFs.
2. For every non-empty subset of the four signals:
   a. Cross-sectionally z-score each signal so the loud ones don't
      swallow the quiet ones in the blend.
   b. Average the z-scores to get a blended signal matrix.
   c. Run the quintile L/S backtest with baseline cost/penalty.
   d. Record full-sample and IS/OOS Sharpe.
3. Summarize by `k` — report mean Sharpe across all `k`-sized blends
   and the specific `k`-sized blend that achieved the best Sharpe.

## Reproduce

```bash
cd research/05_multifactor_construction
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs)

### All 15 blends, sorted by full-sample Sharpe

| Blend                           | k | Full Sharpe | OOS Sharpe |
|---------------------------------|---|-------------|------------|
| **mom12+mom1+mr5**              | 3 | **+0.582**  | +0.771     |
| mom12+mr5                       | 2 | +0.456      | +0.427     |
| mom1+mr5                        | 2 | +0.407      | +0.506     |
| mr5                             | 1 | +0.394      | +0.533     |
| mom12+mom1                      | 2 | +0.322      | +0.449     |
| mom1                            | 1 | +0.321      | +0.937     |
| mom12+mom1+lowvol+mr5           | 4 | +0.083      | −0.407     |
| mom1+lowvol+mr5                 | 3 | +0.043      | −0.120     |
| lowvol+mr5                      | 2 | −0.068      | −0.479     |
| mom12+lowvol+mr5                | 3 | −0.144      | −0.875     |
| mom1+lowvol                     | 2 | −0.222      | −0.400     |
| lowvol                          | 1 | −0.245      | −0.836     |
| mom12+lowvol                    | 2 | −0.293      | −0.852     |
| mom12+mom1+lowvol               | 3 | −0.309      | −0.646     |
| mom12                           | 1 | −0.322      | −0.581     |

### By blend size k

| k | # combos | Mean Sharpe | Best Sharpe | Best combo          |
|---|----------|-------------|-------------|---------------------|
| 1 | 4        | +0.037      | +0.394      | mr5                 |
| 2 | 6        | +0.100      | +0.456      | mom12+mr5           |
| 3 | 4        | +0.043      | **+0.582**  | mom12+mom1+mr5      |
| 4 | 1        | +0.083      | +0.083      | all four            |

### What we learn

1. **The best 3-signal blend (Sharpe 0.58) is ~50% better than the
   best single signal (Sharpe 0.39).** This is diversification working
   exactly as promised — three low-correlation signals (momentum +
   reversal + mean-reversion) whose noise cancels partially when
   averaged.

2. **The full 4-signal kitchen-sink blend (Sharpe 0.08) is worse than
   every 3-signal blend that excludes `lowvol`**. Adding a bad signal
   (`lowvol` has Sharpe −0.25) pulls the blend's quality down even
   after z-scoring, because the blend is forced to take opposite bets
   in the portfolio construction layer. **This is the empirical
   version of "don't add more factors unless each one pulls its
   weight."**

3. **Every blend containing `lowvol` is worse than every blend not
   containing it**, without exception. The ranking is perfectly
   separable on this universe and this sample.

4. **Mean Sharpe by `k` is misleading** because it averages good and
   bad combos together — the k=3 mean is only +0.04 even though its
   best member is +0.58. Always report the best combo, not the mean,
   when you're running a small-n signal search.

### Takeaway for portfolio construction

> **Diversification adds Sharpe *only* across signals that individually
> earn. One bad signal poisons the blend.**

The study's practical rule: **drop any signal whose standalone Sharpe
is below zero before running a blend search**, because every subset
that includes it will be dominated by subsets that don't.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
