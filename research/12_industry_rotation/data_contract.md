# Data contract

This study does not take any user-supplied data. Everything is pulled at
runtime from the Kenneth French data library via `pandas-datareader`.

## Datasets fetched

| ID                         | Dataset                               | Frequency | Units  | Notes |
|----------------------------|---------------------------------------|-----------|--------|-------|
| `fetch_ff_industries(n)`   | `{n}_Industry_Portfolios`             | monthly   | decimal| n∈{5,10,12,17,30,38,48,49} |
| `fetch_ff_momentum_deciles`| `10_Portfolios_Prior_12_2`            | monthly   | decimal| Columns `Lo PRIOR`..`Hi PRIOR` |
| `fetch_ff_op_portfolios`   | `Portfolios_Formed_on_OP`             | monthly   | decimal| Used for OP premium |
| `fetch_ff_inv_portfolios`  | `Portfolios_Formed_on_INV`            | monthly   | decimal| Used for INV premium |

All series are pulled in the raw units Ken French publishes them (percent)
and divided by 100 in `_data/fetch_ff.py` so downstream code sees decimals.

## Index convention

Every fetched DataFrame has a `pd.DatetimeIndex` normalized to the last
calendar day of each month (`MonthEnd(0)`). Source data uses
`PeriodIndex('M')`; we convert in `_normalize_index()` so the panels join
cleanly with panels pulled from yfinance or other sources.

## Offline / air-gapped usage

After the first successful run, all datasets are cached to
`research/data_cache/ff_*.pkl`. A subsequent run with no network access
will read from cache automatically. To force a re-fetch, delete the cache
file.

## License

The Ken French data library is free for academic and research use. See
https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
for terms. This repository redistributes none of the data — we only
redistribute the fetch code.
