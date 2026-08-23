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

Rather than ship a study behind a "WRDS required" wall, this one is a
synthetic demonstration: generate a 50-asset × 240-month universe at a
0.2%-per-month hazard (≈2.4% per year) with a terminal shock drawn from
N(−30%, 10%) — the Shumway (1997) convention for a missing
performance-delisting return — then run the same backtest on (a) the
survivors-only subset and (b) the full delisting-adjusted panel. The
Sharpe gap between the two is the bias.

Only the data is synthetic; the adjustment logic is the standard one.

## What the synthetic run demonstrates

- Survivorship-biased backtests systematically overstate Sharpe (positive
  bias).
- The magnitude depends on the delisting rate and the terminal shock
  magnitude.
- The direction is always positive (you can never be negatively biased
  by dropping the worst performers).

A run on CRSP with the real delisting file would be expected to show the
same sign, at a magnitude that depends on the sample period and the
delisting-return convention chosen.
