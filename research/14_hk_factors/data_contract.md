# Data contract

12 Hong Kong large-caps via yfinance, monthly returns.

Ticker convention: `NNNN.HK` — yfinance routes HK tickers through
Hong Kong Exchange data automatically.

Universe chosen for:
- Deep pre-2015 history (all 12 listed well before the study window)
- Large-cap, liquid, no micro-cap survivorship artifacts
- Sector diversity: financials, tech, telecom, utilities, property,
  industrial, transport, exchange

Cached to `data_cache/hk_<start>_<end>.pkl`.
