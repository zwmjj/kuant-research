# Systematic Alpha Validation Across Asset Classes

**Research question.** Which families of systematic signals survive strict walk-forward validation across heterogeneous asset classes, and what does the pattern of survivors vs. rejections tell us about where tradable alpha actually lives?

## Motivation

It is cheap to find a Sharpe > 1 backtest in a single asset class by cherry-picking lookbacks. It is much harder to find a signal family that generalizes across asset classes *under the same specification* and survives out-of-sample testing. The generalization requirement is the real test — and it is where most published crypto "edges" die.

## Setup

- **Asset classes.** U.S. equities (SPY and sector ETFs), U.S. Treasuries (TLT, SHY, IEF), gold (GLD), crypto majors (BTC, ETH, SOL).
- **Signal families tested.**
  - Adaptive-lookback momentum (dynamically selects best lookback from {10, 20, 40, 60, 100} days by recent Sharpe)
  - Dual momentum (absolute + relative to cash)
  - Short-horizon z-score mean reversion (5-day)
  - Cross-sectional momentum (long top / short bottom tercile, risk-adjusted)
  - Overnight-premium capture
  - Vol-regime and correlation-regime switching
  - Crypto-specific microstructure: weekend effect, Monday reversal, equity-crypto divergence
  - VIX contango filter
- **Validation protocol.** All signals use `shift(1)` to prevent look-ahead. Walk-forward cross-validation with rolling folds; a strategy is accepted only if it produces positive out-of-sample Sharpe in **every** fold and passes an EWMA-Sharpe floor (> 0.3) and 60%+ positive-year rule.
- **Sample.** 2016–2026 daily data; crypto from 2018.

## Findings

### What survived

Adaptive-lookback momentum was the only specification that generalized across every asset class tested:

| Asset     | EWMA Sharpe | Walk-forward OOS folds |
|-----------|------------:|-----------------------:|
| SPY       | **+1.79**   | 10 / 10                |
| TLT       | +1.69       | 10 / 10                |
| GLD       | +1.62       | 10 / 10                |
| BTC-USD   | +1.54       | 17 / 17                |

A greedy uncorrelated portfolio construction (correlation threshold 0.20) selected 5 strategies — the four adaptive momentum sleeves plus crypto cross-sectional momentum — achieving **EWMA Sharpe 2.37** and **out-of-sample Sharpe 2.99**. The gap between realized (2.37) and theoretical upper bound (3.40) implies ~30% correlation drag in practice, a useful diagnostic for how much diversification is actually being captured.

Other survivors (at lower confidence): multi-asset dual-momentum ensemble, correlation-regime allocation, VIX-contango-filtered equities.

### What failed

Crypto temporal "edges" — the kind most commonly cited in retail literature — failed every fold:

- **Weekend effect** — no exploitable return premium
- **Monday reversal** — negative OOS
- **Equity-crypto divergence** — negative OOS (−0.37)

So did vol-of-vol SPY (−0.52) and sector hybrid momentum (−0.62). Risk-parity allocation across the survivors failed the cost-robustness gate (see [`01_cost_robust_portfolio.md`](01_cost_robust_portfolio.md)).

## Implications

1. **In crypto, cross-sectional > temporal.** Cross-sectional momentum (long high-momentum coins, short low-momentum) passed validation; every temporal pattern tested failed. This is consistent with the view that crypto market structure rewards relative-value signals and punishes calendar anomalies that are visible to every retail participant.
2. **Adaptive lookback beats fixed lookback.** Dynamically choosing the momentum lookback by recent Sharpe ratio outperforms any single fixed horizon. The cost of the adaptation is small; the benefit is robustness to regime change (trend speed varies across periods).
3. **Failure is the product.** The framework's value is its rejection rate. Accepting only signals that produce positive Sharpe in *every* walk-forward fold, across asset classes, under a single specification, is what prevents fitted-to-history strategies from reaching capital.

## Limitations

- Adaptive lookback has its own risk of lookback-selection overfitting; the set {10, 20, 40, 60, 100} is a hyperparameter and was not itself cross-validated over larger grids.
- Walk-forward protocol is daily; higher-frequency signals (minute / hour bars) are out of scope here.
- Crypto failure analysis uses 2018+ data; the "weekend effect" literature predates that sample, and the failure may reflect market maturation rather than universal invalidity.

## Status

Signals that passed are components of the live portfolio's strategy pool; the selection criterion documented in `01_cost_robust_portfolio.md` then determines final weights.
