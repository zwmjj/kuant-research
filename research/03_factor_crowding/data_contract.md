# Data contract

Two public sources, no credentials:

- **yfinance** — 10 SPDR sector ETFs, monthly returns (shared cache with
  studies 01 and 08).
- **Kenneth French FF5** — fetched via `pandas-datareader`, cached under
  `research/data_cache/ff5_*.pkl`.

The regression uses the standard `{Mkt-RF, SMB, HML, RMW, CMA}` monthly
panel against the strategy's return stream less the risk-free rate.
