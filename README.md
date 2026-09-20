# Kuant Research

Independent quantitative research on systematic multi-asset portfolio construction, signal validation, and execution-cost-aware alpha selection.

This repository documents the research methodology and empirical findings behind a 14-strategy multi-asset systematic book spanning U.S., U.K., Hong Kong and Korean equity indices, U.S. Treasuries, commodities, G10 FX, and liquid crypto majors — covering trend-following, dual/cross-asset momentum, mean reversion, and macro-regime signals.

**Scope of this repository.** A partial, sanitized view of a larger private research and trading stack. `research/` holds fourteen reproducible offline studies on public data — methodology studies, not the traded strategies. `results/` holds sanitized selection-stage output for the 14 deployed sleeves. Live trading code, execution adapters, credentials, account data, and proprietary signal parameters are intentionally excluded.

**Published figures describe the paper-traded configuration, not the live one.** The live book runs a modified version of these strategies; those modifications, and the resulting live performance, are not published. Any performance figure in this repository belongs to the paper/validation track — it is not the realised result of the live account, and the two are expected to differ.

**Sharpe conventions.** Published research figures are computed net of modelled transaction costs (commission, bid-ask spread, square-root market impact) and gross of volatility targeting and drawdown control. Those overlays are used in live risk management but are excluded from reported research Sharpes, because they redistribute leverage rather than create alpha. Reported Sharpe ratios are return-to-volatility ratios computed **gross of the risk-free rate** (annualised return ÷ annualised volatility, no risk-free deduction). On the deployed configuration this is 20.8 / 9.2 = 2.26; deducting a 4% risk-free rate would give 1.83. The same convention is applied consistently across every study in this repository, so cross-study comparisons are unaffected.

**Capital.** A personal, self-funded account. No external or client capital is managed. Paper trading from August 2025; live since September 2025.

---

## 2026-08 methodology audit — published figures moved

A self-audit found three methodology errors. All three are fixed, and **fixing
them changed results this repository had already published.** That is stated
here rather than left for a reader to discover by diffing
`expected_output.json`.

| Error | What it was | Effect |
|---|---|---|
| Self-financing spreads deducted RF twice | `ff5_regression` subtracted the risk-free rate from a spread that is already self-financing | Alphas were biased **downward**. Study 03's `mr5` alpha moves from −0.0409 to −0.0201 and its t-stat from −0.78 to −0.39; the conclusion changes from "`mr5` is the only positive alpha" to "`mr5` has the largest alpha, and `mom1` is also positive" |
| Lookahead in `_shrink_signal` | `bfill().iloc[0]` back-filled future values into the start of each series | Study 01's `mom12` best-penalty Sharpe falls from **+0.233**; the signal is weaker than reported once the lookahead is removed |
| Sortino used the wrong denominator | Downside deviation was computed about the mean, not the target | Every Sortino figure in all 14 studies changed. This is the single largest source of diffs across `expected_output.json` |

The direction of the first two matters: one had been **understating** alphas and
one had been **overstating** a signal. Neither error was uniformly flattering,
which is why neither was caught by looking at whether results seemed too good.

**Highlight figures in this README were re-checked and still hold** — study 07's
`max_sharpe` trap is 0.253 Sharpe / −16.3% CAGR / −94.15% MDD against the
"+0.25 / −16% / −94%" quoted below. Per-study READMEs carry their own corrected
numbers.

**Reproducibility.** Every input is now frozen under `research/_data_frozen/`
with a MANIFEST, so the 14 studies run offline and cannot silently drift when an
upstream data source changes. `research/_core/test_core.py` covers the fixed
primitives, and `tools/` holds the freeze, re-run/diff, and backend smoke-test
scripts used to produce and verify this.

**One behaviour change to be aware of before upgrading.** `fetch_cn.py`
previously printed and skipped when an index could not be retrieved; it now
retries four times and raises. A partial panel is a different study, so failing
loudly is correct — but an environment that used to complete will now stop.

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
  inflates Sharpe by **+0.135 units** on a synthetic panel calibrated
  to a 2.4%/year delisting rate.

Every study runs in <60 seconds from a fresh clone, produces
`sample_output/results.json`, and diffs against a committed
`expected_output.json` to catch drift on any re-run.

### `methodology/`
Framework documents — the strategy whitepaper and the data-source catalogue.

### [`results/`](results/)
Sanitized selection-stage outputs — the deployed portfolio configuration and the unconstrained max-Sharpe artefact it was chosen *over*. No live P&L or account data. See [`results/README.md`](results/README.md) for what each field means and why the higher-Sharpe solution was not deployed.

---

## Research Principles

1. **Walk-forward first.** Out-of-sample validation under a walk-forward cross-validation protocol (typically 252-day train / 126-day test, rolled forward) is applied wherever the sample length supports it; studies 08 and 09 are explicitly structured around it. Where a study reports full-sample statistics — 01, 03, 04, 06 and 07 — it is labelled as such in its own README, and the figure is treated as a lower bound on over-fitting risk, not as evidence.
2. **Costs are a first-class citizen.** A strategy that is not robust to 2–5bps per-day transaction costs is not a strategy. Cost sensitivity is a pre-deployment gate, not an afterthought.
3. **Drawdown budget over headline Sharpe.** Allocation decisions are anchored on drawdown budget consumption, inter-strategy correlation, and realized-vol scaling — not on picking the highest-Sharpe sleeve.
4. **Failures are findings.** Negative results (e.g. crypto temporal edges failing OOS) are reported alongside positive ones. The value of the research framework is its rejection rate, not its acceptance rate.

---

## Disclaimer

This repository is for research and educational purposes. Nothing here constitutes investment advice. Past walk-forward performance does not imply future results.
