# Transaction-Cost–Aware Portfolio Construction

**Research question.** When combining multiple quantitative strategies into a single multi-asset book, which weighting scheme is most robust to realistic execution costs, and how should the portfolio-selection criterion be designed to reflect that?

## Motivation

Back-tested Sharpe ratios are routinely reported at zero transaction cost. This is a dangerous default: weighting schemes that look dominant on paper (particularly risk parity, which pushes weight onto the lowest-volatility sleeves and therefore requires the highest turnover) can completely invert their ranking once even modest per-trade costs are applied.

The question is not *"does the backtest survive costs?"* — it is *"does the selection criterion itself change under costs?"*

## Setup

- **Universe.** A 12-strategy multi-asset book spanning U.S. Treasuries, precious metals, international equities (U.S., Korea, Hong Kong), FX, sector equities, and liquid crypto majors. Strategy types: trend-following, dual momentum, z-score mean reversion, cross-sectional momentum, yield-curve and macro-regime signals.
- **Sample.** ~1,500 trading days, 2020–2026.
- **Weighting schemes compared.** Equal-weight, risk parity, Sharpe-weighted, max-Sharpe (SLSQP), max-Sharpe at 2bps cost, EWMA Sharpe-weighted.
- **Cost grid.** 0 bps, 2 bps, 5 bps, 10 bps per day.
- **Selection protocol.** For each scheme, compute walk-forward cross-validated Sharpe under each cost assumption; compare gross vs. net rankings.

## Findings

Risk parity — the headline "optimal" construction at zero cost — collapses the fastest under realistic frictions:

| Scheme           | 0 bps  | 2 bps  | 5 bps  |
|------------------|-------:|-------:|-------:|
| Risk parity      | **+2.21** | −1.51 | −7.08 |
| Sharpe-weighted  | +1.95  | **+1.50** | **+0.82** |

At 0bps, risk parity looks dominant (Sharpe 2.21 vs. 1.95). At 2bps, it has already inverted to a losing strategy, while Sharpe-weighted retains 77% of its gross performance. By 5bps, risk parity is deeply negative (−7.08) while Sharpe-weighted is still profitable.

The mechanism is direct: risk parity pushes weight onto the lowest-vol sleeves, which mechanically require the most frequent rebalancing to maintain their vol contribution — so they pay the most in cost. Sharpe-weighted allocation, by contrast, concentrates into strategies whose edge is large relative to their turnover.

Additional checks on the Sharpe-weighted portfolio:

- 6 of 6 positive calendar years (2021–2026)
- 6 of 7 positive walk-forward folds (252/126 train/test)
- Deflated Sharpe Ratio 0.994 (z = 3.14)
- SPY correlation +0.16

## Implications

1. **Selection criterion.** The portfolio-selection score was changed from raw EWMA Sharpe to **cost-adjusted EWMA Sharpe** using a 2bps/day assumption — i.e. `score = EWMA_Sharpe(r − 2/10000)`. This single change flips the recommended scheme from risk parity to Sharpe-weighted.
2. **Pre-deployment gate.** A *cost-robustness gate* was added to the deployment pipeline: any candidate portfolio whose Sharpe at 5bps is negative is automatically rejected, regardless of gross metrics. This alone blocked the risk-parity book from reaching the live account.
3. **What this rules out.** High-frequency mean-reversion sleeves and low-vol sleeves that rely on frequent rebalancing are systematically down-weighted, not because their signals are bad, but because their economics do not survive intra-day costs.

## Limitations

- The 2bps assumption is calibrated to liquid ETF/futures execution on a retail-style venue and understates cost for small-cap single names and illiquid crypto pairs.
- Cost is modeled as a linear per-notional deduction; it does not capture non-linear market impact at scale, and therefore does not substitute for a proper pre-trade TCA model at institutional AUM.
- Walk-forward folds are 252/126; shorter holding-period strategies deserve finer grids.

## Status

Adopted as the live-selection criterion for the production book. Implemented in `optimize_weights.py` and gated in the deployment pipeline prior to order submission.
