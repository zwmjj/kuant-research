# Kuant Research

Independent quantitative research on systematic multi-asset portfolio construction, signal validation, and execution-cost-aware alpha selection.

This repository documents the research methodology and empirical findings behind a 14-strategy multi-asset systematic book spanning U.S./HK equities, U.S. Treasuries, commodities, G10 FX, and liquid crypto majors — covering trend-following, dual/cross-asset momentum, mean reversion, and macro-regime signals.

**Scope of this repository.** A partial, sanitized view of a larger private research and trading stack. `research/` holds fourteen reproducible offline studies on public data — methodology studies, not the traded strategies. `results/` holds sanitized selection-stage output for the 14 deployed sleeves. Live trading code, execution adapters, credentials, account data, and proprietary signal parameters are intentionally excluded.

**Published figures describe the paper-traded configuration, not the live one.** The live book runs a modified version of these strategies; those modifications, and the resulting live performance, are not published. Any performance figure in this repository belongs to the paper/validation track — it is not the realised result of the live account, and the two are expected to differ.

**Sharpe conventions.** Published research figures are computed net of modelled transaction costs (commission, bid-ask spread, square-root market impact) and gross of volatility targeting and drawdown control. Those overlays are used in live risk management but are excluded from reported research Sharpes, because they redistribute leverage rather than create alpha.

**Capital.** A personal, self-funded account. No external or client capital is managed. Paper trading from August 2025; live since September 2025.

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

**All 14 studies shipped and reproducible.** See
[`research/README.md`](research/README.md) for the full catalogue with
one-line headline findings per study, cross-study meta-findings, and
the shared `_core/` / `_data/` infrastructure.

Highlights:

- [`04_regime_timing`](research/04_regime_timing/) — **`mr5` + VIX
  regime filter = Sharpe 0.69, MDD −4.8%.** Best risk-adjusted result
  in the whole book, from public data only.
- [`07_optimization_diminishing`](research/07_optimization_diminishing/) —
  The **`max_sharpe` trap**: unconstrained tangency portfolios report
  +0.25 Sharpe while actually destroying capital (−94% MDD, −16% CAGR)
  via volatility drag.
- [`02_survivorship_bias_impact`](research/02_survivorship_bias_impact/) —
  Synthetic demonstration that a naïve survivorship-biased backtest
  inflates Sharpe by **+0.13 units**, matching the +0.15 reference
  from the WRDS CRSP version in the main Kuant platform.

Every study runs in <60 seconds from a fresh clone, produces
`sample_output/results.json`, and diffs against a committed
`expected_output.json` to catch drift on any re-run.

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
