# Kuant: A Multi-Factor Quantitative Research Platform

**White Paper v1.0** | March 2026

---

## Abstract

Kuant is a full-stack quantitative research platform implementing 28+ factors across US and Chinese equity markets. The platform features event-driven backtesting with realistic transaction cost modeling, Phase 3+4 SOP compliance auditing, cross-market factor analysis, and a web-based IDE for custom strategy development. All results include survivorship bias correction (8,446 delisting returns) and real market impact costs based on CRSP monthly ADV data.

Key findings: (1) Gross Profitability (GPA) is the purest alpha source with lowest factor crowding (R²=0.65); (2) Volatility-of-Volatility (VoV) is the most stable factor with near-zero IS-to-OOS decay; (3) Price-to-Sales achieves the highest OOS Sharpe (1.22) among newly discovered factors; (4) Multi-factor combinations plateau at 3-4 factors — additional factors dilute signals; (5) Cross-market US-CN factor correlations are near zero, offering excellent diversification.

---

## 1. Data & Methodology

### 1.1 Data Sources

| Source | Market | Period | Content |
|--------|--------|--------|---------|
| WRDS/CRSP | US | 2000-2025 | Monthly prices, returns, volume (12,594 permnos) |
| WRDS/Compustat | US | 2000-2025 | Annual fundamentals (130,982 firm-years) |
| WRDS/msedelist | US | 2000-2025 | 23,654 delisting records, 8,446 applied |
| Kenneth French | US | 2000-2025 | FF5 factors, 10-industry portfolios |
| baostock | China | 2010-2025 | CSI300 monthly (300 stocks, 45,630 obs) |

### 1.2 Universe Construction

- US: Stocks with avg price > $5 and >60% data completeness
- Market cap filter: top 25% (US) or top 30% (China)
- After filtering: ~2,149 US stocks, ~234 Chinese stocks

### 1.3 Transaction Cost Model

```
Model: Square-root market impact (Almgren & Chriss)
  MI = k × sqrt(Q / ADV)
  k = 0.3 (conservative; literature range 0.1-0.5)

Components:
  Commission:     1.0 bps (US) / 2.5 bps (China)
  Bid-ask spread: 5.0 bps
  Market impact:  k=0.3, real CRSP ADV
  SEC fee:        0.8 bps on sells (US)
  Stamp tax:      5.0 bps on sells (China)
  Short borrow:   30 bps/year (US only)

Total estimated cost: 15-30 bps per round-trip trade
```

### 1.4 Survivorship Bias Treatment

Following Shumway (1997), we apply delisting returns from CRSP msedelist:
- Performance-related delistings (code 500-599): -30% if return missing
- Mergers/exchanges (code 200-399): 0% if return missing
- Impact: Sharpe ratios decrease 0.08-0.16 across all factors

### 1.5 Signal Construction

All signals use `shift(1)` to prevent lookahead bias. Signals are cross-sectionally ranked to [-1, 1] range. Universe filter applied after ranking.

---

## 2. Factor Library

### 2.1 US Factor Results (Post-Delisting, Real ADV Costs)

#### Tier 1: Effective (Sharpe > 0.9 or strong OOS)

| Factor | Sharpe | IS | OOS | Decay | MDD | Alpha | R² | Source |
|--------|--------|-----|------|-------|------|-------|-----|--------|
| Price-to-Sales | 1.08 | 1.02 | 1.22 | -19% | -38% | +6.9% | 0.78 | Compustat |
| FF5 Alpha | 1.05 | 1.19 | 0.71 | 40% | -51% | +7.3% | 0.69 | Rolling regression |
| GPA | 1.02 | 1.10 | 0.80 | 27% | -36% | +6.7% | 0.65 | Novy-Marx 2013 |
| Leverage Change | 0.98 | 1.05 | 0.74 | 29% | -36% | +5.5% | 0.71 | NEW |
| ROE | 0.93 | 1.08 | 0.58 | 46% | -35% | +4.2% | 0.66 | Hou et al. 2015 |
| Revenue Momentum | 0.92 | 0.88 | 1.04 | -18% | -43% | +3.9% | 0.74 | NEW |
| Mom × Quality | 0.92 | 0.93 | 0.86 | 7% | -38% | +4.2% | 0.68 | Interaction |

#### Tier 2: Marginal (Sharpe 0.5-0.9)

| Factor | Sharpe | OOS | Alpha | Crowding |
|--------|--------|-----|-------|----------|
| Momentum Breadth | 0.89 | 1.24 | +3.1% | Low |
| Asset Growth | 0.86 | 1.03 | +3.6% | Medium |
| 12-1 Momentum | 0.81 | 0.91 | +2.5% | High (UMD=0.61) |
| Earnings-to-Price | 0.76 | 0.72 | +4.0% | High (HML=0.46) |
| Book-to-Market | 0.74 | 1.33 | +5.0% | Very High (R²=0.87) |
| Skewness | 0.78 | 0.80 | +2.8% | Medium |
| Defensive Value | 0.78 | 1.21 | +3.5% | Low |

#### Tier 3: Ineffective

| Factor | Sharpe | Issue |
|--------|--------|-------|
| IVOL | 0.58 | Negative alpha (-1.3%) |
| High-52 | 0.57 | Near-zero alpha (0.2%) |
| Low Vol | 0.45 | Severe OOS decay |
| Mean Reversion | 0.46 | High drawdown (-57%) |

### 2.2 Factor Crowding Analysis

| Factor | R² | Dominant Loading | Assessment |
|--------|-----|-----------------|------------|
| BM | 0.87 | HML = 0.89 | Replicates HML — extremely crowded |
| AG | 0.75 | HML = 0.29 | Moderate crowding |
| EP | 0.74 | HML = 0.46 | Crowded via value |
| P/S | 0.78 | Mixed | Moderate |
| GPA | 0.65 | **None dominant** | **Purest alpha** |
| ROE | 0.66 | None dominant | Clean |
| Mom12 | 0.65 | UMD = 0.61 | Crowded via momentum |

**Orthogonalization** (stripping size + value exposures):
- GPA: R² drops 0.65 → 0.54, OOS Sharpe improves 0.80 → 1.16
- ROE: R² drops 0.66 → 0.57, OOS improves 0.58 → 1.02

### 2.3 Volatility Factor Zoo

8 volatility factors tested. Key findings:
- **Skewness** is the best standalone vol factor (Sharpe=0.78, zero OOS decay)
- **Vol-of-Vol** is most stable (-2% decay) but lower Sharpe (0.72)
- **Vol × Quality combos dramatically outperform** standalone vol: downvol×gpa achieves Sharpe 1.12
- **Low Vol anomaly is weak** after costs (Sharpe 0.45, OOS near zero)

---

## 3. Strategy Optimization

### 3.1 Optimization Layers

| Layer | Technique | Sharpe Impact | MDD Impact |
|-------|-----------|---------------|------------|
| Multi-factor blend | Risk parity across 3-4 factors | +0.07 | -7pp |
| Vol targeting (10%) | Scale exposure inversely to realized vol | +0.02 | -8pp |
| Drawdown control | 3-tier reduction at 10/20/25% DD | 0 | -3pp |
| Orthogonalization | Strip size/value from signals | +0.02 (OOS) | 0 |
| Regime timing | Reduce momentum in high vol | 0 | -2pp |
| **All stacked** | Everything combined | **-0.05** | **Signal dilution** |

**Key insight**: Stacking all layers produces WORSE results than selecting the best 1-2. Multi-factor + vol targeting is the sweet spot.

### 3.2 Best Strategies (Post-Delisting, Real Costs)

| Strategy | Sharpe | IS | OOS | Decay | MDD | Alpha |
|----------|--------|-----|------|-------|------|-------|
| regime_blend (gpa40+roe35+mom25) | 1.09 | 1.22 | 0.79 | 35% | -22% | +6.1% |
| ff5alpha (optimized) | 1.11 | 1.20 | 0.85 | 29% | -28% | +7.3% |
| combo_qvm (new factors) | 1.05 | 1.14 | 0.80 | 17% | -26% | +7.3% |
| orth_blend (gpa60+roe40) | 1.00 | 1.08 | 1.05 | 2% | -24% | +6.0% |
| vol40+gpa60 | 1.17* | — | — | — | -17% | — |

*vol40+gpa60 tested without delisting correction; with correction estimated ~1.05-1.10.

---

## 4. Cross-Market Analysis (US vs China)

### 4.1 A-Share Factor Results (CSI300, Long-Only, baostock)

| Factor | Sharpe | IS | OOS | MDD | Excess/yr |
|--------|--------|-----|------|------|-----------|
| VoV | 0.65 | 0.71 | 0.52 | -22% | +7.7% |
| Downvol (c15) | 0.56 | 0.45 | 0.81 | -28% | +7.8% |
| 6M Momentum | 0.55 | 0.59 | 0.48 | -41% | +8.5% |
| Size (small) | 0.55 | 0.51 | 0.73 | -40% | +10.8% |

### 4.2 Cross-Market Factor Correlation

US-CN factor return correlations are **near zero** (highest: 0.12). This means:
- **Excellent diversification potential** across markets
- Factors are driven by local market microstructure, not global risk
- A dual-market portfolio could significantly reduce drawdowns

### 4.3 Key Differences

| Aspect | US | China |
|--------|-----|-------|
| Best factor | GPA (quality) | VoV (vol stability) |
| Momentum | Works (12-1) | Reversal at index level, momentum at stock level |
| Value (HML) | Moderate (Sh=0.74) | Cycles ±47% every 3 years |
| Low vol | Weak after costs | Stronger but data limited |
| Short selling | Available | Restricted (long-only) |

---

## 5. Execution Model Assessment

### 5.1 Cost Decomposition (GPA factor)

| Component | Sharpe Impact |
|-----------|---------------|
| No cost | 1.079 |
| + Commission (1bp) | -0.002 |
| + Spread (5bp) | -0.005 |
| + Market Impact (k=0.3) | **-0.047** |
| + Borrow (30bp/yr) | -0.003 |
| + SEC fee (0.8bp) | -0.000 |
| **Total net** | **1.022** |

Market impact is the largest single cost, reducing Sharpe by 0.047.

### 5.2 Unmodeled Components

| Missing | Estimated Impact |
|---------|-----------------|
| Dynamic bid-ask spread | -0.02 to -0.05 Sharpe |
| Signal-to-execution delay | -0.01 to -0.03 |
| Partial fills | Negligible at $10K-100K |
| **Total real-world discount** | **Sharpe × 0.85-0.90** |

---

## 6. Compliance & Audit

### Phase 3: Backtest Quality — ALL PASS

| Check | Status | Detail |
|-------|--------|--------|
| P3-F1 Event-driven | PASS | Sequential bar processing |
| P3-F2 Signal separation | PASS | All signals use shift(1) |
| P3-F3 Corporate actions | PASS | CRSP cfacpr + ret |
| P3-C1 Cost completeness | PASS | 5-component sqrt model |
| P3-C2 Conservative costs | PASS | k=0.3, real ADV |

### Phase 4: Independent Review — 5 PASS + 2 WARN

| Check | Status | Detail |
|-------|--------|--------|
| P4-B1 Lookahead | PASS | crash_filter and vol fixed |
| P4-B2 Survivorship | PASS | 8,446 DLRET applied |
| P4-B3 Data snooping | PASS | DSR in gate checks |
| P4-B4 Cost underestimate | PASS | Conservative parameters |
| P4-B5 Execution | WARN | No partial fills |
| P4-B6 Time alignment | PASS | CRSP + yfinance aligned |
| P4-B7 Overfitting | PASS | IS/OOS + DSR |

---

## 7. Research Summary

14 completed research studies covering:

1. **Signal Decay vs Transaction Cost** — Quality signals have 11+ month half-life; momentum only ~5 months
2. **Survivorship Bias** — 8,446 delisting returns reduce all Sharpe ratios by 0.08-0.16
3. **Factor Crowding** — BM is 87% explained by HML; GPA is only 65% (purest alpha)
4. **Regime Timing** — Helps drawdown at portfolio level, not single-factor level
5. **Multi-Factor Construction** — Optimal at 3-4 factors; 6+ causes signal dilution
6. **Execution Model Limits** — Real-world Sharpe discount estimated at 10-15%
7. **Optimization Diminishing Returns** — Multi-factor + vol target is sweet spot
8. **IS/OOS Stability** — Low R² best predicts OOS success (not high IS Sharpe)
9. **Equity Vol Factor Zoo** — 8 vol factors; Skew best standalone, Vol×Quality combos best overall
10. **A-Share Cross-Market** — Value cycles ±47% every 3 years; LowVol strongest
11. **Cross-Market Robustness** — US-CN correlations near zero; excellent diversification
12. **Industry Rotation** — Industry momentum Sharpe=0.23 (weak standalone)
13. **New Factor Discovery** — Price-to-Sales (Sh=1.08), Momentum Breadth (OOS=1.24)
14. **A-Share Stock-Level** — VoV is only 6/6 gate-passing CN factor

---

## 8. Conclusions

1. **Best single factor**: GPA (Gross Profitability) — highest alpha purity, lowest crowding, robust across IS/OOS
2. **Best new factor**: Price-to-Sales — Sharpe 1.08 with OOS improvement to 1.22
3. **Best strategy**: regime_blend (gpa40+roe35+mom25) — Sharpe 1.09, MDD -22%
4. **Optimization limit**: Signal-level optimization reaches Sharpe ~1.1 with MDD ~-22%. Further improvement requires new data sources or execution improvements.
5. **Cross-market opportunity**: US-CN factor correlations near zero — dual-market allocation has significant diversification potential

---

*Generated by Kuant v1.0 | Data: WRDS CRSP/Compustat 2000-2025 + baostock CSI300 2010-2025*
*Cost model: sqrt impact k=0.3, real CRSP ADV, SEC fee, stamp tax, borrow cost*
*Survivorship: 8,446 Shumway-adjusted delisting returns*
