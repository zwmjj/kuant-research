# Kuant Regime-Blend Strategy Whitepaper

**Strategy**: Regime-Blend Multi-Factor Long/Short Equity
**Version**: 2.0
**Date**: April 2026
**Universe**: US Equities (CRSP/Compustat, ~500 tradeable after filters)
**Rebalance**: Monthly (month-end)
**Benchmark**: S&P 500 (SPY)

---

## 1. Executive Summary

Regime-Blend is a monthly-rebalanced long/short equity strategy combining four
well-established academic factors (Gross Profitability, Return on Equity,
12-1 Momentum, and Fama-French 5-Factor Alpha) with dynamic risk management
through volatility targeting, drawdown control, and sigmoid-based regime filtering.

| Metric | Value |
|--------|-------|
| CAGR | 13.2% |
| Sharpe Ratio | 0.84 |
| Sortino Ratio | 1.33 |
| Alpha (vs SPY) | 6.0% p.a. |
| Beta | 0.79 |
| Max Drawdown | -45.5% |
| Win Rate | 63.2% |
| DSR (25 trials) | 0.977 |
| Backtest Period | Jan 2000 - Mar 2026 (315 months) |

---

## 2. Investment Thesis

Alpha comes from three orthogonal sources:

1. **Quality Premium** (GPA + ROE): High-profitability firms generate persistent
   excess returns due to underpricing of earnings quality. GPA (Novy-Marx 2013)
   has R^2 = 0.65 against standard factors, meaning ~35% of its return is
   unexplained by known risk factors -- the purest alpha in our library.

2. **Momentum Premium** (12-1 Month): Cross-sectional momentum (Jegadeesh &
   Titman 1993) captures under-reaction to firm-specific news. We skip the
   most recent month to avoid short-term reversal.

3. **Alpha Extraction** (FF5 Rolling Alpha): Stocks with persistently positive
   alpha relative to Fama-French 5 factors represent mispriced securities the
   standard model fails to explain. 36-month rolling regression isolates this
   residual alpha.

Regime adjustment reduces momentum exposure during high-volatility periods
(momentum crash risk) and slightly increases quality exposure (flight to quality).

---

## 3. Signal Construction

### 3.1 Factor Definitions

| Factor | Weight | Construction | Academic Source |
|--------|--------|-------------|----------------|
| GPA | 25% | Gross Profit / Total Assets | Novy-Marx (2013) |
| ROE | 25% | Net Income / Common Equity | Hou, Xue, Zhang (2015) |
| Mom12-1 | 25% | Cumulative return months t-13 to t-2 | Jegadeesh & Titman (1993) |
| FF5 Alpha | 25% | 36-month rolling intercept vs MKT/SMB/HML/UMD | Fama & French (2015) |

### 3.2 Signal Processing Pipeline

```
Raw fundamental data (Compustat annual, 6-month Fama-French lag)
  -> Factor values per stock per month
  -> Cross-sectional rank [-1, +1] per factor per month
  -> Regime adjustment (reduce momentum in high-vol months)
  -> Risk-parity weighted blend across 4 factors
  -> Final composite signal: cross-sectional rank [-1, +1]
```

### 3.3 Regime Adjustment

Momentum factors suffer from "momentum crashes" (Daniel & Moskowitz 2016)
during volatility spikes. We adjust:

| Market Vol (vs median) | Momentum Scale | Quality Scale |
|------------------------|----------------|---------------|
| > 1.5x | 0.50 | 1.10 |
| 1.2x - 1.5x | 0.75 | 1.00 |
| 0.8x - 1.2x | 1.00 | 1.00 |
| < 0.8x | 1.20 | 0.90 |

Regime is measured using 6-month rolling SPY volatility relative to its
expanding median. All data is available at time of signal generation
(no lookahead bias -- shift(1) applied throughout).

### 3.4 Lookahead Bias Prevention

- **Price data**: All signals use `shift(1)` -- signal at month t uses data up to t-1
- **Fundamental data**: Fama-French convention -- fiscal year Y data available after June Y+1
- **Crash filter**: Uses prior month's return, not current month
- **FF5 alpha**: 36-month regression window ending at t-1

---

## 4. Portfolio Construction

### 4.1 Position Sizing

| Parameter | Value |
|-----------|-------|
| Long positions | 20 stocks |
| Short positions | 10 stocks |
| Gross long exposure | 110% (before scaling) |
| Gross short exposure | 10% (before scaling) |
| Net exposure | ~100% (long-biased) |
| Weighting (long) | Inverse volatility (12-month rolling) |
| Weighting (short) | Equal weight |
| Turnover penalty | 0.25 (reduces unnecessary rebalancing) |

### 4.2 Dynamic Position Scaling (3-Layer)

Position sizing is **fully dynamic**, adjusted monthly through three independent layers:

#### Layer 1: Sigmoid Regime Filter

Replaces hard VIX thresholds with smooth transition to avoid whipsaw:

```
weight = 0.3 + 0.7 / (1 + exp(0.3 * (VIX - 25)))
```

| VIX Level | Position Scale |
|-----------|---------------|
| 12 | 98% |
| 20 | 85% |
| 25 | 60% |
| 30 | 35% |
| 40 | 21% |

Parameters (center=25, steepness=0.3, min_weight=0.3) calibrated via
walk-forward cross-validation to avoid overfitting a single threshold.

#### Layer 2: Volatility Targeting

```
scale = target_vol / realized_vol(6 months)
scale = clip(scale, 0.3, 1.5)
```

- **Target**: 10% annualized portfolio volatility
- **Lookback**: 6 months realized vol
- **Max leverage**: 1.5x (floor: 0.3x)

This is the primary risk management lever. In calm markets, leverage
increases (up to 1.5x). In volatile markets, leverage compresses.

#### Layer 3: Drawdown Control

| Peak-to-Trough Drawdown | Position Scale |
|--------------------------|---------------|
| < 10% | 100% |
| 10% - 20% | 80% |
| 20% - 25% | 50% |
| > 25% | 25% |

#### Combined Effect

Final exposure = Base_exposure x Regime_weight x Vol_scale x DD_scale

Example in current market (April 2026):
- Market vol proxy: 17.1 -> sigmoid weight: 0.80
- Vol target scale: 0.59
- No drawdown (new account)
- **Total scale: 0.47** -> Effective long: 51%, short: 5%

The strategy is currently running at ~50% of full capacity due to
elevated realized volatility.

---

## 5. Rebalancing Frequency

### 5.1 Monthly Rebalance

| Aspect | Detail |
|--------|--------|
| Frequency | Monthly (last business day) |
| Signal generation | T-0 close data -> signal computed overnight |
| Execution | T+1 market open (market orders) |
| Turnover | ~30-40% monthly (reduced by 0.25 turnover penalty) |

### 5.2 Why Monthly

- **Factor decay**: Quality and value factors have IC decay over 1-20 day lags.
  Monthly rebalance captures the bulk of predictive power while keeping
  transaction costs manageable.
- **Fundamental data**: GPA and ROE are annual data mapped monthly.
  Higher-frequency rebalancing adds no new fundamental information.
- **Cost efficiency**: At monthly frequency with sqrt impact model,
  estimated annual transaction cost is 2-4% of NAV.

### 5.3 Intra-Month Adjustments

The dynamic position scaling (Section 4.2) is applied at each monthly rebalance.
No intra-month adjustments are made in the current implementation.
Future enhancement: daily vol-target scaling with weekly execution.

---

## 6. Risk Management

### 6.1 Portfolio-Level Controls

| Control | Threshold | Action |
|---------|-----------|--------|
| Max single position | 10% NAV | Reject order |
| Max gross exposure | 150% NAV | Reject order |
| Max single trade loss | $2,000 | Reject order |
| Max daily trades | 100 | Reject order |
| Sector concentration | 30% | Monitor (yellow alert) |
| Pairwise correlation | > 0.80 | Monitor (orange alert) |
| Drawdown | 10% / 20% / 25% | Reduce to 80% / 50% / 25% |

### 6.2 Factor Risk Controls

| Risk | Mitigation |
|------|------------|
| Momentum crash | Regime filter reduces momentum 50% in high vol |
| Value trap | ROE quality screen filters unprofitable "cheap" stocks |
| Factor crowding | GPA has lowest R^2 (0.65) vs standard factors |
| Multicollinearity | VIF monitoring; orthogonalization available |
| Multiple testing | BH-FDR correction applied; only 2/11 factors survive |

### 6.3 Gate Checks (Pre-Deployment)

| Gate | Threshold | Status |
|------|-----------|--------|
| Sharpe > 0.8 | 0.84 | PASS |
| MDD > -50% | -45.5% | PASS |
| Win Rate > 55% | 63.2% | PASS |
| DSR > 95% (25 trials) | 97.7% | PASS |
| IS/OOS decay < 40% | 4.2% | PASS |

---

## 7. Transaction Cost Model

### 7.1 Cost Components

| Component | Estimate | Model |
|-----------|----------|-------|
| Commission | 1 bps | Fixed per trade |
| Spread | 5 bps | Half-spread 2.5 bps |
| Market impact | k * sqrt(Q/ADV) | Almgren-Chriss, k=0.3 |
| Short borrow | 30 bps/yr | Applied to short notional |
| SEC fee | 0.8 bps | Sell-side only |

### 7.2 Capacity Estimate

Based on held position ADV analysis (SP500 large-cap universe):

| AUM | Participation Rate | One-Way Impact | Annual Cost | Status |
|-----|-------------------|----------------|-------------|--------|
| $10M | 0.03% | 55 bps | 13.3% | Viable |
| $50M | 0.17% | 123 bps | 29.6% | Marginal |
| $100M | 0.34% | 175 bps | 41.9% | High cost |

**Recommended max AUM**: $25-50M for acceptable cost levels.
Strategy is designed for small institutional / family office scale.

---

## 8. Backtest Performance

### 8.1 Summary Statistics (Jan 2000 - Mar 2026)

| Metric | Value |
|--------|-------|
| Total Return | 2,448% ($10K -> $254,779) |
| CAGR | 13.2% |
| Annualized Volatility | 16.4% |
| Sharpe Ratio | 0.84 |
| Sortino Ratio | 1.33 |
| Max Drawdown | -45.5% |
| Calmar Ratio | 0.29 |
| Win Rate | 63.2% |
| Profit/Loss Ratio | 1.10 |
| Max Consecutive Losses | 6 months |
| Alpha (vs SPY) | +6.0% p.a. |
| Beta (vs SPY) | 0.79 |
| VaR (95%) | -6.4% monthly |
| CVaR (95%) | -9.2% monthly |

### 8.2 Annual Returns

| Year | Return | Year | Return | Year | Return |
|------|--------|------|--------|------|--------|
| 2001 | +34.0% | 2010 | +21.4% | 2019 | +37.9% |
| 2002 | +3.9% | 2011 | +10.2% | 2020 | +36.7% |
| 2003 | +24.5% | 2012 | +21.0% | 2021 | +26.3% |
| 2004 | +27.5% | 2013 | +27.7% | 2022 | -18.5% |
| 2005 | +2.9% | 2014 | +16.3% | 2023 | +16.9% |
| 2006 | +12.4% | 2015 | +4.4% | 2024 | +16.6% |
| 2007 | -4.3% | 2016 | -6.4% | 2025 | +15.7% |
| 2008 | -33.7% | 2017 | +25.3% | 2026 | +6.3% (3mo) |
| 2009 | +24.2% | 2018 | +9.4% | | |

Negative years: 2007 (-4.3%), 2008 (-33.7%), 2016 (-6.4%), 2022 (-18.5%)

### 8.3 Walk-Forward Cross-Validation

Rolling 36-month train / 12-month test, 7 folds:

| Metric | Value |
|--------|-------|
| Avg IS Sharpe | 0.84 |
| Avg OOS Sharpe | 0.81 |
| Sharpe Decay | 4.2% |
| Avg Sharpe Retention | 95.8% |
| Aggregate OOS Sharpe | 0.87 |

OOS decay of 4.2% is well within the 40% threshold for low-frequency strategies,
indicating minimal overfitting.

---

## 9. Statistical Rigor

### 9.1 Multiple Testing

- **Factors tested**: 11 (from a library of 31+)
- **Correction method**: Benjamini-Hochberg FDR (alpha=0.05)
- **Pre-correction significant**: 4 factors
- **Post-correction significant**: 2 factors (max_return, volatility)
- **Expected false positives**: 0.55

Note: The regime_blend strategy uses GPA, ROE, Mom12, FF5Alpha -- selected
based on economic rationale and orthogonality, not pure statistical screening.

### 9.2 Newey-West HAC Standard Errors

IC t-statistics computed with heteroskedasticity and autocorrelation consistent
(HAC) standard errors using Newey-West with m = T^(1/3) lags:

| Factor | IC Mean | t-naive | t-Newey-West | Inflation |
|--------|---------|---------|--------------|-----------|
| max_return | 0.082 | 3.08 | 3.34 | 0.92x |
| volatility | 0.075 | 2.69 | 3.01 | 0.89x |
| momentum_12_1 | 0.032 | 1.08 | 1.20 | 0.90x |

t-stat inflation is < 1.0x (negative IC autocorrelation), confirming
naive estimates are conservative in this dataset.

### 9.3 VIF Multicollinearity

| Factor | VIF | Status |
|--------|-----|--------|
| volatility | 65.2 | SEVERE -- shared variance with downside_vol, max_return |
| momentum_12_1 | 10.0 | WARNING |
| skewness | 8.3 | WARNING |
| multi_tf_mom | 4.7 | OK |

**Mitigation**: regime_blend avoids using correlated vol factors together.
Orthogonalization module available for factor purification.

### 9.4 Deflated Sharpe Ratio

- **Observed Sharpe**: 0.84
- **DSR (25 trials)**: 0.977
- **z-score**: 2.00
- **Interpretation**: 97.7% confidence the strategy's Sharpe exceeds
  what would be expected from the best of 25 random strategies.

### 9.5 Regime-Conditional IC

| Factor | Low VIX (<20) | Mid VIX (20-30) | High VIX (>30) |
|--------|---------------|-----------------|----------------|
| max_return | IC=0.09, t=2.87*** | IC=0.01, ns | N/A |
| momentum_12_1 | IC=0.03, ns | IC=0.03, ns | N/A |

**Key finding**: max_return alpha concentrates in low-volatility regimes.
The regime filter correctly reduces exposure during periods where
alpha is statistically absent.

---

## 10. Data Sources

| Data | Source | Coverage | Update |
|------|--------|----------|--------|
| Prices & returns | WRDS CRSP Monthly Stock File | 2000-2026 | Monthly |
| Fundamentals | WRDS Compustat CCM | 2000-2025 | Annual |
| FF5 factors | Ken French Data Library | 2000-2026 | Monthly (2-3 week lag) |
| Delisting returns | WRDS CRSP Delisting File | 2000-2026 | As available |
| Live prices | yfinance (extends WRDS cache) | Latest | Real-time |

### Survivorship Bias Correction

Shumway (1997) methodology applied:
- Performance-related delistings (codes 500-599): assume -30% if dlret missing
- M&A/exchange delistings: assume 0% if dlret missing
- 8,446 delisting events processed

---

## 11. Execution Infrastructure

### 11.1 Live Trading Pipeline

```
[Monthly, T-0 Close]
  1. Load WRDS cache + yfinance extension (latest prices)
  2. Update FF5 from Ken French Data Library
  3. Generate regime_blend signal (4-factor composite)
  4. Apply 3-layer dynamic position scaling
  5. Compute inverse-vol weights (long) + equal weights (short)
  6. Map permno -> ticker via CRSP permno_info

[T+1 Market Open]
  7. Close existing positions via the broker REST API
  8. Submit new orders against the target book
  9. Reconcile target vs actual
  10. Archive signals + reconciliation to JSON
```

### 11.2 Execution Layer

The signal generator and the execution layer are separate processes communicating
through a dated target-book file: the generator writes target weights, the executor
reads them, diffs against the current book, and places the difference. This keeps
research reproducible without a broker connection, and makes every trade traceable
to the exact signal file that produced it.

The layer is broker-agnostic behind a thin adapter interface (submit, cancel,
positions, reconcile). Short availability is a hard pre-trade constraint: names
that fail the borrow check are dropped from the target book before submission
rather than being rejected at the exchange.

Broker identity, account configuration, credentials, order parameters, and the
operational command surface are deliberately not published — this section
describes how execution is structured, not what was executed.

---

## 12. Known Limitations

1. **Signal lag**: FF5 alpha factor has ~1-2 month lag (Ken French publication delay).
   GPA/ROE have 6-18 month lag (annual fundamentals + Fama-French convention).
   This is by design -- Point-in-Time alignment prevents lookahead bias.

2. **2008 drawdown**: -33.7% in 2008 despite regime filter. The filter reduces
   but does not eliminate drawdown. Strategy has long bias (100% net).

3. **Capacity**: Strategy capacity is limited to ~$25-50M due to transaction
   cost scaling with sqrt(participation rate).

4. **No intra-month risk management**: Position scaling only at monthly rebalance.
   Flash crashes or rapid drawdowns within a month are not addressed.

5. **Small-cap exposure**: WRDS universe includes mid/small caps where
   execution costs are higher than modeled.

---

## 13. Future Enhancements

| Enhancement | Expected Impact | Status |
|-------------|----------------|--------|
| Daily vol targeting | Reduce intra-month drawdown | Planned |
| Sentiment overlay | +0.1-0.2 Sharpe | Research |
| IV rank overlay | Better entry timing | Research |
| Cross-market CN/HK factors | Diversification (corr ~0) | Data ready |
| LEAN Engine integration | Institutional backtesting | Infrastructure ready |

---

## Appendix A: Fundamental Law Decomposition

| Factor | IC | Breadth (N x freq) | Predicted IR | Actual IR | Transfer Coef |
|--------|-----|-------------------|-------------|-----------|---------------|
| momentum_12_1 | 0.032 | 360 | 0.61 | 0.10 | 0.17 |
| max_return | 0.082 | 360 | 1.56 | 0.30 | 0.19 |

Transfer Coefficient of ~0.18 indicates significant slippage between
theoretical and realized information ratio, primarily from:
- Transaction costs consuming alpha
- Position constraints (20L/10S) limiting diversification
- Cross-sectional noise in monthly factor ranks

## Appendix B: Strategy Correlation with Existing Factors

| Factor Pair | Correlation |
|-------------|-------------|
| momentum vs volatility | -0.09 |
| momentum vs max_return | 0.26 |
| volatility vs max_return | 0.83 |
| momentum vs skewness | 0.09 |

The 0.83 correlation between volatility and max_return confirms these
measure similar risk characteristics. regime_blend avoids using both
simultaneously, instead using GPA/ROE (fundamentals) + Mom + FF5Alpha
(residual), which are structurally orthogonal.

---

*Document generated by Kuant Quant Framework v2.0*
