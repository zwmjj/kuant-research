# Data contract

Two public sources:

- **yfinance** — 10 SPDR sector ETFs (same cache as 01/03/05/06/07/08)
- **FRED** via `pandas_datareader` — four macro series:
  - `VIXCLS`  — daily VIX
  - `DGS10`   — 10-year Treasury constant-maturity yield
  - `T10Y2Y`  — 10Y minus 2Y yield curve slope
  - `UNRATE`  — U.S. unemployment rate

All macros are resampled to month-end via forward-fill. Cached to
`data_cache/fred_*.pkl`.

FRED API is free and unauthenticated. pandas_datareader talks directly
to the St. Louis Fed's public endpoints.
