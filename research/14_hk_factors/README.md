# 14 · Hong Kong Equity Factors

**Category:** HK / Cross-Market
**Data tier:** 🟢 A — yfinance only, no credentials
**Runtime:** ~30 seconds

---

## Research question

Do the same four reference signals work on a **Hong Kong single-stock
universe**? HK is a useful third data point because:

- It's an Asian market (captures some CN economic exposure) but
  structurally closer to a developed-market microstructure than
  mainland A-shares.
- It has English-speaking, institutional-flow-heavy participants,
  unlike the retail-dominated A-share market tested in study 10.
- The universe (12 HK large-caps) is a genuine single-stock cross
  section, not an index panel — so low-vol and momentum can operate
  on their intended cross-sectional axis.

## Method

Identical to study 11 but with HK single stocks:

1. Pull monthly total returns for 12 HK large-caps via yfinance.
2. Build `mom12 / mom1 / lowvol / mr5` on the 12-name panel.
3. Run the quintile L/S backtest (25% sleeves = 3 longs, 3 shorts).
4. Report full-sample and IS/OOS Sharpe per signal.

## Reproduce

```bash
cd research/14_hk_factors
pip install -r requirements.txt
python run.py
```

## Universe

| Ticker   | Name                      | Sector       |
|----------|---------------------------|--------------|
| 0005.HK  | HSBC Holdings             | Financials   |
| 0700.HK  | Tencent Holdings          | Tech         |
| 0941.HK  | China Mobile              | Telecom      |
| 1299.HK  | AIA Group                 | Insurance    |
| 0001.HK  | CK Hutchison              | Conglomerate |
| 0002.HK  | CLP Holdings              | Utilities    |
| 0003.HK  | HK & China Gas            | Utilities    |
| 0011.HK  | Hang Seng Bank            | Financials   |
| 0016.HK  | Sun Hung Kai Properties   | Property     |
| 0027.HK  | Galaxy Entertainment      | Consumer     |
| 0066.HK  | MTR Corporation           | Transport    |
| 0388.HK  | HKEX                      | Exchange     |

## Key findings (reference run, 2015-12-31 → 2025-12-31, 12 HK large-caps)

| Signal   | Full Sharpe | IS Sharpe | OOS Sharpe | MDD    |
|----------|-------------|-----------|------------|--------|
| `mom12`  | **+0.379**  | **+0.817**| +0.085     | −40.3% |
| `mom1`   | −0.019      | −0.830    | **+0.533** | −59.1% |
| `lowvol` | −0.160      | −0.647    | +0.175     | −50.7% |
| `mr5`    | −0.236      | −0.634    | +0.064     | −68.3% |

### The HK universe breaks `mr5`

This is the first study in the research book where `mr5` — the
champion of studies 01, 03, 05, 08, 11 — produces a **negative
full-sample Sharpe**. HK 12-name L/S: `mr5` returns −0.24.

This is important for calibrating how much to trust the other 5
studies' `mr5` wins. HK is a single-stock universe (not an index or
ETF panel), which means:

- Idiosyncratic single-name risk dominates
- Mean reversion is noisier when an individual stock's return is a
  much bigger chunk of the cross-section than a sector's
- 12 names is half the width of the A-share index panel in study 10,
  further reducing the reliability of quintile ranks

**Conclusion**: `mr5`'s edge is more fragile than 5-out-of-6 studies
suggested. It's still the most consistent winner across *aggregate*
(ETF/index) universes, but breaks down on narrow single-stock panels.

### `mom12` is the HK champion

+0.38 full Sharpe, IS +0.82 — by far the strongest momentum result
in the research book. HK medium-term momentum is consistent with what
everyone who has traded HK equities anecdotally reports: the market
trends cleanly at medium horizons, probably because of the high
institutional / mainland-flow influence.

But the IS→OOS decay is severe: +0.82 IS drops to +0.09 OOS. The
medium-term HK momentum edge is shrinking in real-time. By 2025 the
OOS Sharpe is effectively flat. Whether that represents regime change
or the late-sample noise of a 48-month OOS window is the next study.

### `mom1` pattern: IS−, OOS+ — same story as US and CN

HK mom1 repeats the post-2020 mean-reversion strengthening seen in
both US and CN. Three independent markets showing the same
structural shift at the same time is probably **not noise** — likely
a genuine post-2020 liquidity/microstructure change (higher retail
participation, lower market-maker inventory, faster ETF flows)
translating to more short-term mean reversion in single-stock
returns.

### Implications for the signal library

> **Rank-based quintile L/S methodology is not universal.** Short-term
> mean reversion (`mr5`, `mom1`) works on panels with enough
> cross-sectional breadth for the quintile ranks to mean something
> (5+ tradeable names per sleeve) and less well on narrow universes.
> Medium-term momentum (`mom12`) works on markets with strong
> institutional trending behavior (HK, pre-2020 US) and less well on
> retail-driven or recently-turbulent markets.

The one-size-fits-all hope that a single signal would win on every
universe doesn't survive the HK test. This is actually a feature:
it says the research protocol is detecting real per-market structure
rather than smoothing it into a single meaningless average.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
