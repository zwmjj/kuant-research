# Data Sources

Catalogue of the data used across this repository: what each source provides,
what period it covers, how it is obtained, and where its limitations bite the
research. Sources are labelled by *tier*: A is fully public and reproducible
from a fresh clone, B is public but rate-limited or served by an unofficial
endpoint, and C requires a licensed subscription. No study in this repository
publishes a tier-C result — the C row is listed because studies expose an
opt-in hook for readers who do hold a subscription.

---

## 1. Sources used in this repository

| Source | Market | Content | Frequency | Access | Tier |
|---|---|---|---|---|---|
| **Kenneth French Data Library** | U.S. | FF3/FF5 factors, industry portfolios, momentum deciles | Monthly | Public, no credentials (`pandas_datareader.famafrench`, Dartmouth archives) | A |
| **yfinance** | U.S., global ETFs | Adjusted close, volume | Daily | Public, no credentials; unofficial endpoint | B |
| **akshare** | China A-share | CSI/SSE index levels | Daily | Public, no credentials; per-IP rate limits | B |
| **FRED (St. Louis Fed)** | U.S. macro | Yield-curve, volatility and credit-spread series | Daily | Public, no credentials (`pandas_datareader`) | A |
| **Synthetic panels** | — | Delisting-bias and crowding simulations | Monthly | Generated in-repo from a pinned seed | A |
| **WRDS CRSP / Compustat** | U.S. | Monthly stock file, delisting file, fundamentals | Monthly / annual | Institutional subscription; credentials read from the environment | C |

Fetchers live in [`research/_data/`](../research/_data/), and every one of them
reads [`research/_data_frozen/`](../research/_data_frozen/) before it considers
going to the network. The frozen panels are committed CSVs with a manifest
recording the source, the fetch date, a SHA-256 and the coverage of each — so a
fresh clone reproduces every published figure with **no network access at all**,
and a published figure stays checkable after the upstream endpoint changes.
`research/data_cache/` remains as an unversioned local working cache; when both
exist the frozen copy wins.

No fetcher in this repository touches a licensed vendor: where a study offers a
CRSP backend it is an opt-in hook inside that study's own `data.py`, guarded on
`WRDS_USERNAME` / `WRDS_PASSWORD` being present, and the study's headline result
is always the public-data version.

### Why the public backend is the published one

A CRSP-backed result is not reproducible by a reader without a subscription,
which makes it unfalsifiable in practice. Every headline figure in
`research/` is therefore computed on tier A or tier B data, and where a
licensed backend would materially change the answer, the study says so in its
own `data_contract.md` rather than quietly reporting the licensed number.

---

## 2. Coverage and known gaps

| Limitation | Where it bites | Consequence |
|---|---|---|
| No point-in-time A-share index membership | Study 10, Study 11 | Residual survivorship bias in the CN panel, estimated at ~2% of annualised return |
| No A-share fundamentals (ROE, book-to-market) | Study 10 | CN factor set is restricted to price-based signals; no value or quality sleeve |
| Monthly frequency on the U.S. panel | Studies 01, 06 | Execution-cost modelling is calibrated, not measured; intraday participation effects are outside the sample |
| No implied-volatility surface | Study 09 | Volatility factors use realised volatility only |
| No analyst estimates | Study 13 | No SUE or post-earnings-announcement-drift signal |
| No A-share limit-up/limit-down flags at index level | Study 10 | Tradability of extreme daily moves is not modelled |
| yfinance and akshare are unofficial endpoints | Studies 01, 03, 09, 10, 11, 12, 14 | Schema and availability can change without notice; the pinned cache in `data_cache/` is what guarantees a reproducible re-run, not the upstream API |

These are limits on what can be concluded, not defects to be worked around.
Where a study's finding would flip under better data, that is stated in the
study's own README under *Limitations*.

---

## 3. Survivorship and delisting treatment

Study 02 is the reference implementation. Delisting returns follow the
Shumway (1997) convention: performance-related delistings (CRSP codes
500–599) are assigned −30% where the delisting return is missing;
M&A and exchange-move delistings are assigned 0%. The larger −55% figure
sometimes quoted for this adjustment comes from Shumway & Warther (1999)
and applies to Nasdaq specifically — the two should not be used
interchangeably.

Because the public backend has no delisting file, study 02 runs on a
synthetic panel calibrated to a 2.4%/year delisting rate rather than on
CRSP. It measures the *size and direction* of the bias under a known
data-generating process; it does not measure the historical U.S. bias.

---

## 4. Reproducing a study

```bash
cd research/<study>
pip install -r requirements.txt
python run.py
```

Every run is offline: the study reads the frozen panel committed under
`research/_data_frozen/`. Each run writes `sample_output/results.json` and diffs
it against the committed `expected_output.json`, exiting non-zero on any metric
drift beyond 1e-3. To confirm the offline claim rather than take it on trust,
disconnect the network and run any study — it must still pass its own gate.
Source, universe, date range, and every parameter are pinned in that
study's `config.yaml`; the contract each fetcher must satisfy is documented
in its `data_contract.md`.
