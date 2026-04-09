# Quantitative Portfolio Manager — Profile

**Role.** Independent Portfolio Manager, systematic multi-asset book.
**Location.** Cambridge, United Kingdom.
**Tenure.** September 2025 – Present.

> This document is the public summary of a privately operated systematic portfolio. It deliberately omits live P&L, account identifiers, broker configuration, specific signal parameters, execution plumbing, and any information that could be reverse-engineered into a tradable signal. For the underlying research methodology, see [`research/`](research/) and [`methodology/`](methodology/).

---

## Mandate

Sole portfolio manager of a live multi-asset systematic book combining 14 strategies across U.S./HK equities, U.S. Treasuries, commodities (precious metals, industrial metals, energy, agri), G10 FX, and liquid crypto majors. Full ownership of the research pipeline, allocation framework, risk budget, and execution.

The book is deliberately multi-strategy and multi-asset rather than concentrated: the design premise is that a book of moderately-correlated, cost-robust sleeves outperforms a single high-Sharpe sleeve on a drawdown-adjusted basis over a full cycle.

## Strategy Families

The portfolio combines, at the family level:

- **Trend-following** on rates and commodities
- **Dual and cross-asset momentum** on equities, metals, and crypto
- **Mean reversion** on FX, sector equities, and agri commodities
- **Macro-regime signals** — yield-curve steepness, central-bank policy state, equity-index regime

Individual strategy specifications, lookbacks, and parameter grids are not published. At the aggregate level, inter-strategy correlations to SPY range from roughly −0.27 to +0.33, providing structural diversification.

## Portfolio Construction

Allocation is driven by a **cost-adjusted EWMA Sharpe** criterion — individual-sleeve weights are optimized under a realistic 2bps/day execution-cost assumption, not on raw backtest Sharpe. See [`research/01_cost_robust_portfolio.md`](research/01_cost_robust_portfolio.md) for why this matters; the short version is that the "best" weighting scheme under zero cost (risk parity) inverts to losing under 2bps, while Sharpe-weighted allocation remains profitable through 5bps.

Positions are re-sized using:

- Realized-volatility scaling per sleeve
- Inter-strategy correlation penalties to avoid crowding
- Drawdown-budget consumption as a dynamic throttle
- Portfolio-level volatility targeting with gross/net exposure caps
- Regime-aware de-risking overlays

## Risk Framework

- **Vol target** anchored at a fixed portfolio-level figure with monthly recalibration.
- **Drawdown budget** consumed linearly; breaches of sleeve-level budgets trigger automatic re-weighting rather than discretionary override.
- **Cost-robustness gate** applied pre-deployment: any candidate configuration whose Sharpe at 5bps is negative is rejected, regardless of gross metrics.
- **Walk-forward validation** on every signal: 252/126 train/test rolled forward, all-folds-positive rule.
- **Correlation stress**: the observed correlation drag (~30%) relative to the theoretical uncorrelated upper bound is tracked as a diagnostic for diversification decay.

## Execution & Operations

- Cloud-native execution stack against a broker REST API; scheduled rebalancing and hourly portfolio/risk monitoring.
- Pre-trade risk checks, post-trade reconciliation, and alerting are automated.
- All signals use `shift(1)` to eliminate look-ahead bias from research to production.
- Operational runbook, audit protocol, and strategy pre-deployment checklist are documented under [`methodology/`](methodology/).

## Research Pipeline

The research process that feeds this book is documented in this repository:

- [`research/01_cost_robust_portfolio.md`](research/01_cost_robust_portfolio.md) — Why the selection criterion is cost-adjusted EWMA Sharpe, not raw Sharpe.
- [`research/02_cross_asset_alpha.md`](research/02_cross_asset_alpha.md) — Which signal families survived walk-forward validation across asset classes, and why crypto temporal edges failed.
- [`methodology/STRATEGY_WHITEPAPER.md`](methodology/STRATEGY_WHITEPAPER.md) — Full strategy framework.
- [`methodology/STRATEGY_CHECKLIST.md`](methodology/STRATEGY_CHECKLIST.md) — Pre-deployment gates.
- [`methodology/STAT_AUDIT_RESULT.md`](methodology/STAT_AUDIT_RESULT.md) — Statistical audit results.

## What Is Not In This Repository

- Live P&L series, account balances, position sizes, or broker identifiers
- Specific signal parameters, lookbacks, or thresholds
- Execution code, order-routing logic, credentials, or environment configuration
- Any data that could be reverse-engineered into a tradable signal

These are maintained separately and are not publishable.

---

## Disclaimer

This document describes the scope and methodology of a privately operated portfolio for research and professional-profile purposes only. Nothing here constitutes investment advice, a solicitation, or a representation of future performance. Walk-forward backtest figures cited in linked research documents are out-of-sample under the stated protocol but are not guarantees.
