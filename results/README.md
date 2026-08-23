# Selection-stage outputs

Two sanitized artefacts from the sleeve-selection stage. Neither is live
account data: there is no P&L series, no position size, and no account
information in this folder.

## `final_portfolio_config.json` — the deployed configuration

The 14 sleeves actually deployed, their weights, each sleeve's EWMA Sharpe,
and its correlation to SPY. Headline figures:

| Field | Value | Meaning |
|---|---|---|
| `sharpe_eq` | 2.255 | Annualised return ÷ annualised volatility, **gross of the risk-free rate** (20.8 / 9.2). Deducting a 4% risk-free rate gives 1.83. |
| `sharpe_ewma` | 2.812 | Same ratio computed on EWMA-weighted moments, which over-weights the recent sample |
| `theoretical_sr` | 3.509 | What the same sleeves would produce if mutually uncorrelated — the gap to 2.255 is the correlation drag, ≈36% |
| `wfcv_oos` | 2.841 | Walk-forward out-of-sample figure from the selection stage |
| `max_dd` | −10.4 | Maximum drawdown, % |

These are **selection-stage backtest figures for the published
configuration**, not realised trading results. They are what the chosen
sleeve set produced over the selection sample under the stated cost model.
Realised paper-trading performance differs from them, and the live book
runs a modified version of these strategies that is not published — so
three distinct numbers exist and only this one is in the repository.

## `optimal_weights.json` — an artefact, not the deployment

This file is the **unconstrained max-Sharpe solution over 16 candidate
sleeves** at a 2bps/day cost assumption. It is not what was deployed, and
the difference is deliberate:

- It contains 16 sleeves; the deployed book has 14. `ll_ftse` and
  `fed_ease` were candidates that did not survive selection.
- Its reported Sharpe of 2.654 is **higher** than the deployed 2.255. That
  is the point. [`research/07_optimization_diminishing/`](../research/07_optimization_diminishing/)
  is the public-data study of exactly this failure mode: at a small sleeve
  count, an unconstrained tangency portfolio posts the best Sharpe on the
  estimation sample while concentrating risk badly enough to destroy the
  capital path. On the public four-signal panel in that study the same
  method reports a +0.25 Sharpe alongside a −94% drawdown.
- The deployed book therefore uses Sharpe-proportional weights
  (`"weighting": "sharpe_wt"`) with correlation and drawdown-budget
  constraints, accepting a 0.4 lower selection-stage Sharpe in exchange for
  a weight vector that does not depend on inverting an ill-conditioned
  covariance estimate.

The file is kept in the repository because deleting the losing branch of a
comparison is how selection bias gets in.
