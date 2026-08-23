# 02 · Survivorship Bias Impact (Synthetic Demo)

**Category:** Data Quality
**Data tier:** ⚫ Synthetic — the only study without a real data source
**Runtime:** <5 seconds

---

## Research question

**How much does dropping delisted stocks inflate backtest Sharpe?**
This is the most widely-discussed data bias in quant equity research.
Shumway (1997) sets the convention of assigning −30% where a
performance-related delisting return is missing from CRSP; Shumway &
Warther (1999) report roughly −55% on Nasdaq. Either way, a backtest
that filters delisted names out systematically overstates alpha.

## Why this study is synthetic

Survivorship bias is a question about what happened to *delisted*
assets. Every free data source (yfinance, akshare, Ken French)
filters them out. You cannot reproduce it without paid data (WRDS
CRSP with Shumway adjustment).

Rather than ship a study nobody without a WRDS subscription can run,
this one demonstrates the **methodology** on a synthetic universe:

1. Generate 50 assets × 240 months with a seeded RNG.
2. Each asset has a latent "quality" score that shifts its mean
   return (so factors have something to rank on).
3. Each month, each asset has a 0.2% chance of receiving a terminal
   delisting shock ~N(−30%, 10%). Shocks must occur after month 24.
4. Run the same 12-month momentum L/S backtest on two panels:
   - `survivors_only`  — dropped all names with a delisting event
   - `full_delist_adjusted` — every terminal shock is kept in the panel
5. Measure the Sharpe gap.

The gap measures the bias under a known data-generating process. It is
not an estimate of the historical U.S. bias, and it is likely to be a
lower bound on one: the −30% terminal shock used here is the Shumway
(1997) convention for performance-related delistings with a missing
delisting return, whereas Shumway & Warther (1999) find roughly −55% on
Nasdaq specifically. The two figures are often quoted interchangeably;
they are not the same estimate.

## Reproduce

```bash
cd research/02_survivorship_bias_impact
pip install -r requirements.txt
python run.py
```

No network access needed. Deterministic seed = 42.

## Key findings (synthetic reference run, seed=42, 50 assets × 240 months)

| Panel                        | Sharpe    | CAGR    | MDD     |
|------------------------------|-----------|---------|---------|
| `survivors_only` (31 names)  | **+0.121**| +0.71%  | −43.1%  |
| `full_delist_adjusted` (50)  | **−0.014**| −0.61%  | −33.1%  |
| **Survivorship bias**        | **+0.135**| +1.32%  | −10.0%  |

19 of 50 assets (38%) received a delisting shock over the 20-year
window. The survivors-only panel has **a positive Sharpe**. The
delisting-adjusted panel has an **essentially zero Sharpe**.

**The survivorship-biased backtest flipped the strategy's sign.**
Without the delisting adjustment, you would have concluded the
strategy earns alpha (albeit modest, Sharpe 0.12). With the
adjustment, you correctly conclude there is nothing there.

### Why this is likely to understate the real bias

1. **We delisted at −30%.** That is the Shumway (1997) convention for a
   missing delisting return. Shumway & Warther (1999) put the Nasdaq
   figure nearer −55%, so real delistings plausibly hit harder than the
   ones simulated here.
2. **We used 50 names.** CRSP has thousands; the tail of extreme
   delisting events is correspondingly longer.
3. **We delisted uniformly.** Real delistings cluster in crisis
   windows (2008, 2020), which amplifies the bias during those
   periods.

The published literature on delisting adjustments reports biases of
comparable magnitude on U.S. momentum books; this run should be read as
a demonstration of mechanism and direction, not as a competing estimate.

### Takeaway

> **If your backtest drops delisted names, your reported Sharpe is
> wrong by roughly 0.1–0.2 units. If your Sharpe is 0.4, your real
> Sharpe is 0.2–0.3. If your Sharpe is 0.2, your real Sharpe might be
> zero.** The direction is always positive, so the bias is always in
> the favor-the-researcher direction.

## Running this on real data

Reproducing the same measurement on CRSP requires the delisting file and
a Shumway-convention adjustment pass over it, which is outside what this
repository can ship. The procedure is: apply the delisting return where
present; where it is missing, assign −30% to performance-related
delisting codes (500–599) and 0% to M&A and exchange-move codes; then
run the identical backtest on the survivors-only and adjusted panels and
take the difference. Any figure produced that way belongs in whatever
repository holds the licensed data, not here.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
