# Kuant Research

Independent quantitative research on systematic multi-asset portfolio construction, signal validation, and execution-cost-aware alpha selection.

This repository documents the research methodology and empirical findings behind a 14-strategy multi-asset systematic book spanning U.S./HK equities, U.S. Treasuries, commodities, G10 FX, and liquid crypto majors — covering trend-following, dual/cross-asset momentum, mean reversion, and macro-regime signals.

> **Scope of this repo.** Methodology, walk-forward results, and strategy-selection logic only. Live trading code, execution adapters, credentials, account data, and proprietary signal parameters are intentionally excluded.

---

## Contents

### [`PORTFOLIO_MANAGER_PROFILE.md`](PORTFOLIO_MANAGER_PROFILE.md)
Public profile of the Quantitative Portfolio Manager role — mandate, strategy families, portfolio-construction framework, and risk methodology. No live P&L, account data, or signal parameters.

### `research/`
**Fourteen reproducible empirical studies** — each shipped as a
self-contained folder with `run.py`, `config.yaml`, `signals.py`,
`expected_output.json`, and a human-readable `README.md` covering the
research question, method, and findings.

See [`research/README.md`](research/README.md) for the full catalogue,
reproducibility protocol, and shared infrastructure (`_core/` backtest
primitives and `_data/` public fetchers).

**Phase 1 — reproducible now:**

- [`01_signal_decay_vs_cost`](research/01_signal_decay_vs_cost/) —
  **Signal Decay vs Transaction Cost.** How a signal's persistence
  determines its maximum tolerable cost budget; demonstrated on 10
  sector ETFs (yfinance) with an optional WRDS CRSP backend.
- [`10_cn_factors`](research/10_cn_factors/) —
  **A-Share Factor Proxies.** Five long-short factor proxies built from
  public style indices via `akshare`; full regime analysis and
  cross-market correlation to US.
- [`12_industry_rotation`](research/12_industry_rotation/) —
  **Industry Rotation via Ken French.** 12-month industry momentum L/S
  plus reference OP / INV / decile-spread premia, all from the public
  Dartmouth data library.

Each study runs in ~30 seconds, produces a JSON output, and diffs
against a committed `expected_output.json` to catch drift. Phase 2
(the remaining 11 studies) is in progress.

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
