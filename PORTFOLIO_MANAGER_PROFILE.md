# Quantitative Portfolio Manager — Profile

**Role.** Independent Portfolio Manager, systematic multi-asset book.
**Location.** Cambridge, United Kingdom.
**Tenure.** September 2025 – Present.

**Scope.** Public summary of a **personal, self-funded** systematic book — no external or client capital is managed. Paper trading from August 2025; live since September 2025. This document deliberately omits live P&L, account identifiers, broker configuration, specific signal parameters, execution plumbing, and any information that could be reverse-engineered into a tradable signal. Performance figures published in this repository describe the **paper-traded** configuration; the live book runs a modified version that is not published, and the two are expected to differ. For the underlying research methodology see [`research/`](research/), and for full reporting conventions see the Scope & Disclosure note in the [README](README.md).

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

Allocation is driven by a **cost-adjusted EWMA Sharpe** criterion — individual-sleeve weights are optimized under a realistic 2bps/day execution-cost assumption, not on raw backtest Sharpe. The reason is that the "best" weighting scheme under zero cost inverts to losing under 2bps, while Sharpe-weighted allocation remains profitable through 5bps; see [`research/07_optimization_diminishing/`](research/07_optimization_diminishing/) for the analogous result on public data, where mean-variance optimization posts the highest Sharpe while producing a −94% drawdown.

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

- [`research/README.md`](research/README.md) — Full catalogue of the fourteen reproducible studies, with the reproducibility protocol and shared cost model.
- [`research/01_signal_decay_vs_cost/`](research/01_signal_decay_vs_cost/) — How far transaction cost erodes each signal, and which remain deployable.
- [`research/06_execution_model/`](research/06_execution_model/) — Sensitivity of reported Sharpe to the execution-cost assumption, across seven scenarios.
- [`research/07_optimization_diminishing/`](research/07_optimization_diminishing/) — Why allocation optimization is negative value-add at small signal counts.
- [`research/11_cross_market_robustness/`](research/11_cross_market_robustness/) — Which signal families hold across U.S. and China A-share markets.
- [`methodology/STRATEGY_WHITEPAPER.md`](methodology/STRATEGY_WHITEPAPER.md) — Reference framework for a separate single-strategy equity study.

## What Is Not In This Repository

- Live P&L series, account balances, position sizes, or broker identifiers
- Specific signal parameters, lookbacks, or thresholds
- Execution code, order-routing logic, credentials, or environment configuration
- Any data that could be reverse-engineered into a tradable signal

These are maintained separately and are not publishable.

---

## Disclaimer

This document describes the scope and methodology of a privately operated portfolio for research and professional-profile purposes only. Nothing here constitutes investment advice, a solicitation, or a representation of future performance. Walk-forward backtest figures cited in linked research documents are out-of-sample under the stated protocol but are not guarantees.
