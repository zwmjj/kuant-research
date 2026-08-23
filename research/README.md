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
- ⚫ **Synthetic** — no market data at all; the panel is generated
  in-repo from a pinned seed to isolate one mechanism under a known
  data-generating process.

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

The `mr5` (5-month z-scored mean reversion) signal appears as a candidate
in eight studies (#01, #03, #04, #05, #06, #08, #11, #14) and is the
strongest of the four candidates in six of them (#03, #05, #06, #08, and
both #04 and the U.S. panel of #11). The three qualifications matter as
much as the count: in #01 it is *not* the highest-Sharpe signal — `mom1`
is — but it is the only one whose Sharpe *rises* as the cost penalty rises,
which is what "cost-robust" means here; in the A-share panel of #11 it
finishes second to `mom1` by 0.01 of Sharpe; and in #14 it fails outright
on HK single stocks, the worst of the four. The HK failure narrows the
domain rather than invalidating the finding, but it is a failure.

The single best deployment recipe the whole research book supports is **`mr5` + `risk_on_only` VIX regime filter** on
sector ETFs, producing a Sharpe of 0.69 and MDD of only −4.8% —
the best risk-adjusted result in the catalogue.

The research book also produces several strong **negative findings**
that should influence deployment decisions: `max_sharpe` portfolio
optimization destroys capital despite a positive Sharpe (#07);
macro-conditioned signals are overfitting amplifiers on small samples
(#13); vol-based factors fail on cross-asset ETF universes (#09);
naive survivorship-biased backtests inflate Sharpe by +0.135 units
on a synthetic panel (#02).

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

Intentionally small (517 lines total). Everything is keyed off a
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

**⚫ Synthetic studies** — study 02 uses no market data. Its panel is
generated in-repo from a pinned seed, calibrated to a stated delisting
rate, so the mechanism it measures is separated from any question about
data quality. It measures the size and direction of the bias under a
known process; it does not measure the historical U.S. bias.

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

- **One split date, stated up front.** Studies that report an IS/OOS
  split use 2020-12-31 so cross-study numbers compare cleanly (#05, #08,
  #10, #11, #12, #14). Studies #01, #03, #04, #06 and #07 report
  full-sample statistics — they sweep a parameter rather than test
  generalisation — and say so in their own README.
- **Costs are a first-class citizen.** The `_core/costs.py` module is
  shared across every study that does a backtest; cost sensitivity is
  always in the output.
- **Failures are findings.** Negative results (e.g. `lowvol` failing in
  the 10-ETF universe in `01_signal_decay_vs_cost`) are reported
  alongside positive ones. The point isn't to sell an alpha, it's to
  produce honest public empirical work.
- **A small universe bounds the claim, it does not excuse it.** These
  studies run on ten-to-fourteen-name panels, which is enough to trace a
  shape and not enough to estimate a premium. Where a wider universe would
  plausibly change the answer, the study says so under *Limitations*
  rather than implying the finding scales.

## License and data terms

- Kenneth French data: free for academic and research use.
- akshare: free scraper of public Sina/Tencent data.
- yfinance: free scraper of Yahoo Finance (best-effort, terms of service
  apply).
- WRDS / CRSP / Compustat (if you use them via Tier B/C): subject to
  your own academic or institutional license. Nothing in this repo
  redistributes licensed data.
