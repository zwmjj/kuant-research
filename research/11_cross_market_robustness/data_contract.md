# Data contract

Two universes, two public data sources:

| Market | Source   | Universe                                  |
|--------|----------|-------------------------------------------|
| US     | yfinance | 10 SPDR sector ETFs                       |
| CN     | akshare  | 8 A-share style indices (CSI/GEM/Value..) |

Both are monthly returns, decimal. Cache shared with study 01
(US ETFs) and study 10 (CN indices).

No WRDS, no Bloomberg, no Compustat. The study's whole point is that
signal methodology can be tested across markets using entirely public
data — anyone can reproduce the comparison.
