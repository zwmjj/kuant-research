# 10 · A-Share Factor Proxies via Style Indices

**Category:** Factor Research / Cross-Market
**Data tier:** 🟢 A — `akshare` only, no credentials, no WRDS
**Runtime:** ~60 seconds (dominated by akshare HTTP latency on first run)

---

## Research question

A-share factor research is hard because clean fundamental panels (ROE,
asset growth, BM) are harder to get outside WRDS/CSMAR licensing. **Can
we recover the same factor signals cheaply by differencing public Chinese
style indices?** If yes, any retail researcher can reproduce results that
would otherwise need a paid data subscription.

And once we have those proxy factors, do they behave like their U.S.
counterparts? Specifically:

1. Does the A-share **Value** factor (Value − Growth) still earn a
   premium in the 2010–2025 sample?
2. Is there an A-share **SMB** (CSI500 − CSI300) premium?
3. Does **Low-Vol** (LowVol index − CSI300) still deliver a positive
   excess return?
4. How correlated are A-share index returns to the U.S. market, and does
   that correlation shift in U.S. high-vol regimes?

## Method

1. Pull 8 public A-share indices from akshare: CSI300/500/1000, ChiNext,
   SSE Value, SSE Growth, Dividend, Low-Vol.
2. Resample to monthly returns, clip to 2010-01-31 onward.
3. Construct 5 long-short factor proxies:
   - `SMB_CN`     = CSI500 − CSI300
   - `HML_CN`     = Value − Growth
   - `LowVol_CN`  = LowVol − CSI300
   - `Div_CN`     = Dividend − CSI300
   - `Growth_CN`  = GEM − CSI300
4. Compute Sharpe / CAGR / MDD / IS-OOS split / rolling 3Y for each.
5. Pull U.S. market return from Fama-French 5 (`Mkt-RF + RF`) and compute
   a cross-market correlation matrix.
6. Define a U.S. high-vol regime as 6-month-rolling US-market vol above
   its expanding median; compute A-share Sharpe within each regime.
7. Slice `HML_CN` into 3-year windows to visualize the value/growth
   cycle; label each window by which side won.
8. Report rolling Low-Vol performance across 3 non-overlapping periods.

## How to reproduce

```bash
cd research/10_cn_factors
pip install -r requirements.txt
python run.py
```

First run pulls ~8 index histories from akshare and caches them to
`research/data_cache/cn_*.pkl`. Subsequent runs are offline.

## Parameters

`config.yaml` surfaces:

- `start_date` — first month kept after resample (default 2010-01-31)
- `end_date`   — last month kept
- `is_oos_split` — IS/OOS pivot (default 2020-12-31, consistent with
  every other study in the repo)
- `indices`    — label → akshare symbol mapping (extend to add more)
- `rolling_windows` — 3-year windows for rolling Sharpe
- `us_regime`  — whether to include the U.S. vol-regime cross-analysis
- `value_growth_cycle_windows` — periods for the V/G cycle chart

## Key findings (reference run, 2010-01-31 → 2025-12-31)

### Factor proxy performance

| Factor     | n   | Full Sharpe | IS    | OOS   | CAGR   | MDD     |
|------------|-----|-------------|-------|-------|--------|---------|
| SMB_CN     | 192 | +0.161      | +0.035| +0.531| +1.3%  | −43.4%  |
| HML_CN     | 192 | −0.004      | −0.231| +0.357| −1.2%  | −51.7%  |
| LowVol_CN* | 53  | +0.926      | +0.926| (n/a) | +5.7%  | −5.4%   |
| Div_CN*    |109  | +0.408      | +0.408| (n/a) | +2.3%  | −10.9%  |
| Growth_CN  | 186 | +0.288      | +0.266| +0.374| +4.1%  | −48.8%  |

&nbsp;&nbsp;&nbsp;&nbsp;\* The LowVol and Dividend series **end early**, not
late: LowVol covers 2012-02 → 2016-06 (53 months) and Dividend covers
2010-01 → 2019-01 (109 months), while every other series in the panel runs
to 2025-12. Both therefore terminate before the 2020-12-31 IS/OOS split, so
no OOS Sharpe exists for either and their full-sample figures are not
comparable with the rest of the table.

### Value/Growth cycle — very long cycles, very clear

| Window  | Cum. return of (Value − Growth) | Winner  |
|---------|---------------------------------|---------|
| 2010-12 | −0.8%                           | Growth  |
| 2013-15 | +6.8%                           | Value   |
| 2016-18 | +16.0%                          | Value   |
| 2019-21 | **−45.4%**                      | Growth (COVID tech rally) |
| 2022-25 | +23.3%                          | Value (post-hike reversal) |

### What we learn

1. **The full-sample HML_CN Sharpe rounds to zero (−0.004)** — A-share
   value/growth is *pure* regime-dependent alpha, not a premium. Any
   factor book that ran HML_CN naked through 2019–2021 lost 45% of
   notional. The post-2022 recovery partially offsets the COVID-era
   drawdown.

2. **U.S.–A-share correlation is higher than often claimed: 0.50**
   at the CSI300/US-market pair, rising to 0.60 for CSI500. A-shares are
   not the uncorrelated diversifier global-macro textbooks sometimes
   suggest — they are closer to a high-beta, lagged version of global
   risk assets. The diversification benefit is smaller than nominal
   correlation-matrix entries suggest once you condition on regime.

3. **SMB_CN is the cleanest OOS story in the panel.** IS Sharpe 0.03,
   OOS Sharpe 0.53 — a 17× jump. Large-cap CSI300 held up through COVID
   while small/mid (CSI500) caught the 2023–2025 rally. This is the
   opposite of the U.S. SMB story and is the single most interesting
   finding in this study.

4. **LowVol_CN's 0.93 Sharpe is a 2012–2016 artefact, not a live result.**
   The series covers 53 months ending June 2016 — it never saw 2018, the
   2020 crash, or the post-2022 regime. It is reported for completeness and
   should not be read as evidence of a low-volatility premium in A-shares;
   the same is true, less severely, of Div_CN, which stops in January 2019.
   Restoring these two to the panel needs a replacement data source with
   continuous coverage, not a re-run of this study.

5. **Growth_CN (GEM − CSI300) improved OOS** (0.37 vs 0.27 IS) —
   ChiNext didn't collapse post-2022 the way U.S. small-cap growth did.

## Files

```
README.md
run.py                — entry point
config.yaml           — parameters
signals.py            — factor proxy construction
requirements.txt
data_contract.md
expected_output.json  — reference numerics
sample_output/        — regenerated each run
```

## Data sources

| Source  | Content                     | License |
|---------|-----------------------------|---------|
| akshare | A-share index daily closes  | Public |
| French  | U.S. FF5 (for cross-corr)   | Public |

akshare scrapes from free sources (Sina, Tencent) — occasionally one of
the symbols returns empty or errors out. The fetcher logs and skips any
failing index rather than crashing; results still compute from whatever
subset succeeded.
