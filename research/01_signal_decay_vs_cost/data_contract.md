# Data contract

Two backends, both returning the same shape:

```
pd.DataFrame(
    index=DatetimeIndex at month-end,
    columns=asset IDs (tickers for yfinance, permno strings for CRSP),
    values=monthly total returns in decimal,
)
```

## Backend 1 — yfinance (default)

No credentials. Downloads adjusted close for the 10 SPDR sector ETFs:

    XLK XLF XLE XLV XLY XLP XLI XLB XLU XLRE

Resamples to month-end (`ME`) and computes `pct_change`. Cached to
`research/data_cache/sector_etf_<start>_<end>.pkl`.

Known limitations:
- XLRE inception is October 2015, which is why the default `start_date`
  in config.yaml is 2015-12-31.
- yfinance occasionally returns incomplete data; the loader will drop
  any all-NaN rows but will not impute missing values.

## Backend 2 — WRDS CRSP monthly (`--source wrds`)

Requires:
- `wrds` Python package installed
- `WRDS_USERNAME` / `WRDS_PASSWORD` exported in the environment

Query: `SELECT date, permno, ret FROM crsp.msf WHERE ...` — pulls the
full monthly return series, pivots to wide, drops permno with <24
observations to stabilize quintile ranks.

This backend is included as a reference implementation; the Kuant main
platform uses a richer pipeline with delisting adjustments (Shumway 1997),
which this simplified version intentionally does not replicate. The
shape of the cost/Sharpe trade-off is the same either way; the absolute
Sharpe levels will differ.

## Why both?

The study's core finding — that signal persistence determines a
strategy's cost budget — is a property of the *signal*, not the
universe. You can see the shape on 10 ETFs just as clearly as on
3,000 CRSP stocks. The yfinance backend makes the study fully
reproducible for anyone without WRDS access; the WRDS backend is there
if you want to verify on institutional-grade data.
