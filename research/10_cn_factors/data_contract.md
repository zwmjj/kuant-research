# Data contract

No user-supplied data. Pulls two public sources at runtime.

## akshare — A-share style indices

| Label    | akshare symbol | Description                 |
|----------|----------------|-----------------------------|
| CSI300   | sh000300       | Large-cap benchmark         |
| CSI500   | sh000905       | Mid-cap benchmark           |
| CSI1000  | sh000852       | Small-cap benchmark         |
| GEM      | sz399006       | ChiNext growth board        |
| Value    | sh000029       | SSE 180 Value               |
| Growth   | sh000030       | SSE 180 Growth              |
| Dividend | sh000922       | CSI Dividend                |
| LowVol   | sh000803       | SSE 180 Low Volatility      |

Each index returns daily OHLCV; `fetch_cn_indices` keeps the `close`,
resamples to month-end and computes `pct_change`. Monthly returns are
stored as decimals.

`akshare.stock_zh_index_daily` scrapes free upstream sources and can
occasionally error on a symbol. The fetcher logs and skips such cases
rather than failing the whole study. Missing coverage downgrades the
number of factors the run reports, not its correctness.

## pandas-datareader — Fama-French 5

Used only for the cross-market correlation and the U.S. vol-regime
cross-analysis. `Mkt-RF + RF` reconstructs the U.S. market return in
excess-plus-risk-free form.

## Cache

Both sources are memoized to `research/data_cache/`. Delete the relevant
pickle to force a re-fetch.

## No credentials required

Neither source needs login. The whole study runs in any environment with
outbound HTTPS to the upstream providers (Sina/Tencent for akshare,
Dartmouth for Ken French).
