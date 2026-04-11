# Data contract

**Daily** (not monthly) returns for a 20-ETF universe, pulled via yfinance.

Universe covers:
- 10 SPDR sectors (XLK/XLF/XLE/XLV/XLY/XLP/XLI/XLB/XLU/XLRE)
- 4 broad US equity (SPY, QQQ, IWM, EEM)
- 3 fixed income (TLT, HYG, LQD)
- 3 commodity (GLD, SLV, USO)

Vol factors need daily data for stable rolling estimates — a 12-month
vol on monthly returns is a 12-observation sample, which is too noisy
to rank cross-sectionally. With daily data we get 252 observations per
12-month window.

Cached to `research/data_cache/etf_daily_*.pkl`. Not shared with the
monthly cache because the cache key encodes the full ticker set.
