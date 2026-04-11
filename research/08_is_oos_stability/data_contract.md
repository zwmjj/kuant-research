# Data contract

Same as `01_signal_decay_vs_cost` — 10 SPDR sector ETFs pulled via
yfinance, monthly returns, month-end DatetimeIndex, decimals.

Cached to `research/data_cache/sector_etf_<start>_<end>.pkl` and
shared across both studies, so running #01 then #08 back-to-back only
downloads the data once.

No credentials. No WRDS hook here — for the full CRSP version of the
IS/OOS analysis, see the WRDS backend in `01_signal_decay_vs_cost/data.py`.
