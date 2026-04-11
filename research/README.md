# Kuant Research — Reproducible Studies

Fourteen empirical studies covering factor research, execution/cost
analysis, cross-market robustness, and portfolio construction. Every
study in this folder is laid out to a common template so you can
**clone this repo, `pip install`, and reproduce the numbers**.

## Quickstart

```bash
git clone https://github.com/zwmjj/kuant-research.git
cd kuant-research/research/12_industry_rotation
pip install -r requirements.txt
python run.py
# → sample_output/results.json + summary.txt
# → reproducibility check against expected_output.json
```

Each study is self-contained in its own folder. You only need to install
the requirements of the study you're running.

## Study catalogue

Legend:
- 🟢 **Tier A** — fully public data, no credentials. Clone → install → run.
- 🟡 **Tier B** — default-public with a WRDS hook for institutional
  reproduction. Runs out-of-the-box on a public fallback universe; point
  `--source wrds` at CRSP for the full version.
- 🔴 **Tier C** — WRDS CRSP/Compustat required. Public fallback not yet
  implemented.

| # | Study | Category | Tier | Status | Headline finding |
|---|-------|----------|------|--------|-------------------|
| 01 | [Signal Decay vs Transaction Cost](01_signal_decay_vs_cost/) | Execution | 🟡 | ✅ | `mr5` most cost-robust; `mom12` best frozen |
| 02 | [Survivorship Bias Impact](02_survivorship_bias_impact/) | Data Quality | ⚫ synth | ✅ | +0.135 Sharpe bias from naive filter |
| 03 | [Factor Crowding](03_factor_crowding/) | Factor Research | 🟡 | ✅ | `mr5` only signal with positive α (not significant) |
| 04 | [Regime Timing](04_regime_timing/) | Portfolio Construction | 🟢 | ✅ | **`mr5`+`risk_on_only` Sharpe 0.69** ⭐ book champion |
| 05 | [Multi-Factor Construction](05_multifactor_construction/) | Portfolio Construction | 🟡 | ✅ | Best 3-blend 0.58 > any pair 0.46 > any single 0.39 |
| 06 | [Execution Model](06_execution_model/) | Execution | 🟡 | ✅ | `mom1` loses 81% of Sharpe in crisis costs |
| 07 | [Optimization Diminishing Returns](07_optimization_diminishing/) | Portfolio Construction | 🟡 | ✅ | **`max_sharpe` trap**: +0.25 SR, −94% MDD |
| 08 | [IS vs OOS Stability](08_is_oos_stability/) | Validation | 🟡 | ✅ | `mr5` only signal that generalizes (IS 0.32 → OOS 0.41) |
| 09 | [Equity Vol Factors](09_equity_vol_factors/) | Factor Research | 🟡 | ✅ | All 5 vol factors lose cross-asset (wrong universe) |
| 10 | [A-Share Factor Proxies](10_cn_factors/) | A-Share / Cross-Market | 🟢 | ✅ | SMB_CN IS=0.04 → OOS=0.53; HML_CN regime-dependent |
| 11 | [Cross-Market Robustness (US vs CN)](11_cross_market_robustness/) | Cross-Market | 🟡 | ✅ | 3/4 signals sign-agree US vs CN; cross-corr ≈ 0 |
| 12 | [Industry Rotation](12_industry_rotation/) | Sector | 🟢 | ✅ | Industry mom Sharpe 0.24 stable IS/OOS; OP prem 0.47 |
| 13 | [New Factors (FRED Macro)](13_new_factors/) | Factor Research | 🟡 | ✅ | Macro conditioners amplify overfitting post-2020 |
| 14 | [HK Equity Factors](14_hk_factors/) | HK / Cross-Market | 🟢 | ✅ | `mom12` +0.38 (strongest in book); `mr5` breaks on HK |

**All 14 studies shipped.** Every folder contains `README.md`,
`run.py`, `config.yaml`, `signals.py`, `requirements.txt`,
`data_contract.md`, `expected_output.json` — seven-file uniform
template with reproducibility gate.

### Cross-study meta-findings

The `mr5` (5-month z-scored mean reversion) signal wins **4 of 5**
studies where it appears as a candidate, and the one where it breaks
(HK single-stocks in #14) narrows the domain rather than invalidating
the finding. The single best deployment recipe the whole research
book supports is **`mr5` + `risk_on_only` VIX regime filter** on
sector ETFs, producing a Sharpe of 0.69 and MDD of only −4.8% —
the best risk-adjusted result in the catalogue.

The research book also produces several strong **negative findings**
that should influence deployment decisions: `max_sharpe` portfolio
optimization destroys capital despite a positive Sharpe (#07);
macro-conditioned signals are overfitting amplifiers on small samples
(#13); vol-based factors fail on cross-asset ETF universes (#09);
naive survivorship-biased backtests inflate Sharpe by ~0.15 units
(#02).

## Template

Every completed study ships the same set of files so the navigation is
uniform:

```
NN_study_name/
├── README.md            # research question, method, findings
├── run.py               # entry point — always `python run.py`
├── config.yaml          # tunable parameters (safe to edit)
├── signals.py           # signal-generation source code
├── data.py              # (only if study has custom data loading)
├── requirements.txt     # minimal pip deps for just this study
├── data_contract.md     # input schema, source, license
├── expected_output.json # reference run — reproducibility gate
└── sample_output/       # regenerated on every run, .gitignored
    ├── results.json
    └── summary.txt
```

`run.py` always:
1. Reads `config.yaml`
2. Loads data (using the shared `_core`/`_data` libraries)
3. Runs the analysis and writes `sample_output/results.json`
4. Diffs the new run against `expected_output.json` and fails with a
   non-zero exit code if any metric drifts beyond `1e-3`.

The reproducibility gate is the most important part — it means any
external contributor can open a pull request confident that a run on
their machine will match yours.

## Shared infrastructure

Every study imports from two shared packages:

### `research/_core/` — backtesting primitives

```python
from research._core import (
    compute_metrics,             # Sharpe/CAGR/MDD/IS-OOS
    split_is_oos,
    rolling_windows,
    long_short_quintile_backtest, # standard L/S engine
    CostConfig,
    load_returns_panel,          # three-source loader
)
```

Intentionally small (~400 lines total). Everything is keyed off a
returns-matrix input contract — if you have a DataFrame of periodic
returns, you have enough to run any study's backtest.

### `research/_data/` — public data fetchers

```python
from research._data import (
    fetch_ff5,                  # Fama-French 5 factors
    fetch_ff_industries,        # 10/12/17/30/48-industry portfolios
    fetch_ff_momentum_deciles,
    fetch_cn_indices,           # akshare A-share indices
)
```

All fetchers cache their output to `research/data_cache/<name>.pkl`,
so subsequent runs are offline. Nothing in this subpackage hits any
licensed vendor.

## Data tiers explained

**🟢 Tier A studies** — depend only on:
- Kenneth French Data Library (public, free)
- akshare A-share indices (public, free via Sina/Tencent)
- yfinance (public, free, best-effort)

These studies are fully reproducible from a fresh checkout with no
accounts, no tokens, no institutional subscriptions.

**🟡 Tier B studies** — depend on a private source (CRSP/Compustat) for
their *canonical* run, but ship a **public fallback** that reproduces the
same qualitative finding on a reduced universe. The study's README
documents what's the same and what's different between the two
backends. You opt into the full version with a command-line flag:

    python run.py --source wrds   # requires WRDS_USERNAME / WRDS_PASSWORD

**🔴 Tier C studies** — depend on CRSP delisting-adjusted returns or
Compustat fundamentals. For now, these are stubs — running them
without WRDS credentials will print a clear error telling you what's
missing. They will be re-tiered to 🟡 as Phase 2 adds public fallbacks.

## How to add a new study

1. Copy an existing folder as a template: `cp -r research/12_industry_rotation research/NN_new_study`
2. Edit README / config / signals / run for the new topic.
3. First run writes `sample_output/results.json` — copy it to
   `expected_output.json` once you've verified the numbers are right.
4. Update the catalogue table at the top of this file.
5. Update `data_contract.md` with the schema of your input.

The goal is: **fifteen minutes from `git clone` to reproduced result**,
for any study in the catalogue, on any machine with network access.

## Reproducibility philosophy

- **Walk-forward first.** Every study splits IS/OOS at 2020-12-31 by
  default so cross-study numbers compare cleanly.
- **Costs are a first-class citizen.** The `_core/costs.py` module is
  shared across every study that does a backtest; cost sensitivity is
  always in the output.
- **Failures are findings.** Negative results (e.g. `lowvol` failing in
  the 10-ETF universe in `01_signal_decay_vs_cost`) are reported
  alongside positive ones. The point isn't to sell an alpha, it's to
  produce honest public empirical work.
- **Small universes are fine for reproducibility.** Every public-
  fallback study carries a footnote explaining what changes on the
  full CRSP universe, so you can trust the shape of the finding.

## License and data terms

- Code: see repository `LICENSE`.
- Kenneth French data: free for academic and research use.
- akshare: free scraper of public Sina/Tencent data.
- yfinance: free scraper of Yahoo Finance (best-effort, terms of service
  apply).
- WRDS / CRSP / Compustat (if you use them via Tier B/C): subject to
  your own academic or institutional license. Nothing in this repo
  redistributes licensed data.
