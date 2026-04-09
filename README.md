# Kuant Research

Independent quantitative research on systematic multi-asset portfolio construction, signal validation, and execution-cost-aware alpha selection.

This repository documents the research methodology and empirical findings behind a 14-strategy multi-asset systematic book spanning U.S./HK equities, U.S. Treasuries, commodities, G10 FX, and liquid crypto majors — covering trend-following, dual/cross-asset momentum, mean reversion, and macro-regime signals.

> **Scope of this repo.** Methodology, walk-forward results, and strategy-selection logic only. Live trading code, execution adapters, credentials, account data, and proprietary signal parameters are intentionally excluded.

---

## Contents

### `research/`
Empirical writeups — research question, method, findings, implications.

- [`01_cost_robust_portfolio.md`](research/01_cost_robust_portfolio.md) — **Transaction-Cost–Aware Portfolio Construction.** How high-turnover weighting schemes collapse under realistic execution costs, and why cost-adjusted EWMA Sharpe should be the portfolio-selection criterion.
- [`02_cross_asset_alpha.md`](research/02_cross_asset_alpha.md) — **Systematic Alpha Validation Across Asset Classes.** Walk-forward validation of momentum, reversal, and microstructure signals across equities, Treasuries, gold, and crypto; cross-sectional vs. temporal edges in crypto.

### `methodology/`
Framework documents — strategy whitepaper, audit protocol, data-source catalog, and the strategy-review checklist used as a pre-deployment gate.

### `results/`
Sanitized outputs — final portfolio configuration and optimal weights from the walk-forward selection stage. No live P&L or account data.

---

## Research Principles

1. **Walk-forward first.** Every result reported here is out-of-sample under a walk-forward cross-validation protocol (typically 252-day train / 126-day test, rolled forward). In-sample Sharpe is treated as a lower bound on over-fitting risk, not as evidence.
2. **Costs are a first-class citizen.** A strategy that is not robust to 2–5bps per-day transaction costs is not a strategy. Cost sensitivity is a pre-deployment gate, not an afterthought.
3. **Drawdown budget over headline Sharpe.** Allocation decisions are anchored on drawdown budget consumption, inter-strategy correlation, and realized-vol scaling — not on picking the highest-Sharpe sleeve.
4. **Failures are findings.** Negative results (e.g. crypto temporal edges failing OOS) are reported alongside positive ones. The value of the research framework is its rejection rate, not its acceptance rate.

---

## Disclaimer

This repository is for research and educational purposes. Nothing here constitutes investment advice. Past walk-forward performance does not imply future results.
