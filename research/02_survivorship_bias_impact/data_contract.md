# Data contract

**This study does not use any external data.** The entire input is a
deterministic synthetic universe generated inside `signals.py` using a
seeded numpy RNG.

## Why synthetic?

Survivorship bias is, by definition, a question about what happened
to *delisted* assets — and every public free data source (yfinance,
akshare, Ken French) filters them out at the source. You cannot
reproduce this study on public data; the real CRSP-with-delisting
panel requires WRDS access and a Shumway 1997 adjustment pass.

Rather than ship a Tier C study with a "WRDS required" wall, we ship
a synthetic demonstration: generate a 50-asset × 240-month universe
with a ~5%-per-year delisting rate and a −30% terminal shock (matching
the Shumway empirical average), then run the same backtest on (a) the
survivors-only subset and (b) the full delisting-adjusted panel. The
Sharpe gap between the two is the bias.

The **methodology** is identical to the WRDS version in
`quant/qf/data.py` in the main Kuant platform. Only the data is
synthetic.

## What the synthetic run demonstrates

- Survivorship-biased backtests systematically overstate Sharpe (positive
  bias).
- The magnitude depends on the delisting rate and the terminal shock
  magnitude.
- The direction is always positive (you can never be negatively biased
  by dropping the worst performers).

Anyone running the real WRDS version will see the same signs, slightly
different magnitudes depending on the sample.
