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

Query: `crsp.msf` joined to `crsp.msp500list` for **point-in-time** index
membership, to `crsp.msenames` for the standard US common-stock screen
(`shrcd` 10/11, `exchcd` 1/2/3), and left-joined to `crsp.msedelist` for the
delisting return. Returns are delisting-adjusted on the Shumway (1997)
convention — `(1 + ret) * (1 + dlret) - 1`, with a missing `dlret` filled at
-30% for performance-related codes (500-599) and 0% otherwise. The result is
pivoted wide and permno with fewer than 24 observations are dropped to
stabilise quintile ranks.

Membership is point-in-time deliberately: taking today's S&P 500 list and
running it backwards is the survivorship bias study 02 measures, and it is
worth several tenths of a Sharpe.

**Status: interface, not a published result.** No figure in this repository
is computed from this backend — every headline number comes from the public
yfinance path, because a CRSP-backed number cannot be checked by a reader
without a subscription. The query is written to standard CRSP schema, and the
delisting arithmetic is unit-tested in `research/_core/test_core.py`, but the
repository ships no evidence that the query itself has been executed. Treat it
as a starting point to adapt rather than a tested path.

## Why both?

The study's core finding — that signal persistence determines a
strategy's cost budget — is a property of the *signal*, not the
universe, so a 10-ETF panel is enough to trace the shape. The yfinance
backend makes the study reproducible by anyone, which is why it is the
published one. The CRSP backend exists so that someone with a
subscription can check whether the same shape holds on a single-stock
universe; this repository does not claim to know that it does.
