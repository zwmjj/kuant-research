# Data contract

Two yfinance pulls:
- 10 SPDR sector ETFs (monthly, shared cache with 01/03/05/06/07/08)
- `^VIX` daily close — yfinance serves the CBOE Volatility Index
  symbol directly. The study resamples to month-end and smooths
  with a 12-month moving average.

No credentials. The `^VIX` fetch is tiny (<50 KB) and not cached
separately — yfinance is the source of truth each run.
