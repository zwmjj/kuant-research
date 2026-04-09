# Kuant 诚实审计报告

**日期**: 2026-04-04
**方法**: 所有 Sharpe 均为 RAW（含交易成本，无 vol targeting，无 DD control）

---

## 1. Sharpe 2.0+ 虚高来源

| 来源 | 报告值 | 真实值 | 虚高原因 |
|------|--------|--------|----------|
| `backtest_result.csv` | **2.06** | 0.90 | Vol targeting 压缩分母，月度 std 3.75% vs 真实 4.50% |
| `paper_trading.py` | **2.15** | ~0.95 | 模拟数据 + 短样本(8个月) SE=1.22，随机波动 |
| `max_sharpe.py` 目标 | **1.50+** | 0.84 | Vol target 6% + DD control 删除最差月份 |
| `optimized_live.py` | **1.19** | 0.84 | AUDIT_REPORT 报的是 IS Sharpe，非 raw |

### 虚高机制链

```
Raw alpha Sharpe 0.84-0.96
  + vol targeting (10%):  压缩 vol 分母 → Sharpe 1.2-1.3
  + drawdown control:     删除最差月份 → Sharpe 1.3-1.5
  + 6% vol target:        极端压缩 → Sharpe 1.5-2.0
  + 短样本:               8个月 SE=1.22 → 随机到 2.0-2.5
```

**Vol targeting 不创造 alpha** — 它只是重新分配杠杆。Sharpe 提升是 mechanical artifact，
Quant 面试中报 vol-managed Sharpe 会被直接拒绝。

---

## 2. 诚实因子表现（Raw Sharpe，含 sqrt 交易成本）

**参数**: 20L/20S, L115/S15, turnover penalty 0.25, 2000-2026

| 因子 | Raw Sharpe | CAGR | MDD | Alpha | 来源 |
|------|-----------|------|-----|-------|------|
| **GPA** | **0.84** | 12.7% | -33.4% | +4.4% | Novy-Marx 2013 |
| **ROE** | **0.82** | 10.7% | -37.9% | +3.0% | Hou-Xue-Zhang 2015 |
| AG | 0.63 | 9.0% | -52.1% | -1.0% | Cooper 2008 |
| EP | 0.53 | 9.0% | -47.8% | -1.8% | Basu 1977 |
| Mom12 | 0.41 | 5.6% | -66.3% | -1.1% | J&T 1993 |

GPA 和 ROE 是唯二有正 alpha 且 Sharpe > 0.8 的因子。

---

## 3. 诚实组合表现

**参数**: 20L/10S, L120/S20, turnover penalty 0.25, sqrt costs

| 组合 | Raw Sharpe | CAGR | MDD | 改进 vs baseline |
|------|-----------|------|-----|-----------------|
| regime_blend (旧最优) | 0.847 | 13.7% | -42.7% | baseline |
| **gpa_mom_v2** (GPA70+Mom30) | **0.960** | 14.5% | -31.5% | +13% SR, -11pp MDD |
| **gpa_mom_ep** (GPA63+Mom27+EP10) | **0.974** | 15.0% | **-23.8%** | **+15% SR, -19pp MDD** |

---

## 4. 多资产多频率组合

| 策略 | 资产类 | 频率 | Raw Sharpe | 年化 | MDD | 和 equity 相关性 |
|------|--------|------|-----------|------|-----|-----------------|
| Equity VPD combo | 美股 L/S | 日频 | **1.48** | 31.1% | -17% | — |
| Gold trend | GLD | 日频 | **0.92** | 18.0% | -14% | 0.04 |
| Equity monthly | 美股 L/S | 月频 | **0.97** | 15.0% | -24% | ~0.3 (同资产) |
| Bond rotation | TLT/SHY | 日频 | -0.29 | — | — | -0.08 |
| Crypto vol | BTC | 日频 | -0.92 | — | — | -0.01 |

### Sharpe-weighted 最优组合: Equity 61% + Gold 38%

| 指标 | 单策略 (equity) | 多资产组合 | 提升 |
|------|----------------|-----------|------|
| **Sharpe** | 1.48 | **1.70** | +15% |
| **年化收益** | 31.1% | 25.8% | -5pp (分散化成本) |
| **MDD** | -17.0% | **-8.5%** | **-50%** |

---

## 5. 最终推荐配置

### 月频策略（WRDS 数据）
```
策略:    gpa_mom_ep (GPA 63% + Momentum 27% + E/P 10%)
持仓:    20 long / 10 short
杠杆:    L120% / S20% (gross 140%, net 100%)
换手惩罚: 0.25
成本模型: sqrt (Almgren-Chriss, k=0.3)
Raw Sharpe: 0.974
```

### 日频策略（yfinance 数据）
```
策略:    VPD combo (量价背离40% + 美元成交额30% + Amihud20% + 量突变10%)
持仓:    5 long / 5 short (top/bottom 10%)
频率:    daily signal(T) -> trade(T+1)
Raw Sharpe: 1.48
```

### 多资产层（Alpaca 执行）
```
分配:    Equity 61% + Gold (GLD) 38% + 预留 1%
组合 Sharpe: 1.70
组合 MDD:    -8.5%
```

---

## 6. 环节检查清单

| 环节 | 状态 | 问题 |
|------|------|------|
| 数据 (WRDS CRSP) | ✅ | Survivorship bias 已处理, PIT 对齐 |
| 数据 (yfinance) | ✅ | 补充到最新月份 |
| 数据 (FF5) | ✅ | Ken French 更新到 2026-02 |
| 因子构建 | ✅ | shift(1) 避免 lookahead |
| 截面排名 | ✅ | cross_sectional_rank + cap_quantile filter |
| 交易成本 | ✅ | sqrt model, commission 1bp, spread 5bp |
| 回测引擎 | ⚠️ | run_event_driven 在 bar T 同时生成信号和执行，不需额外 shift |
| Vol targeting | ⚠️ | 不创造 alpha，仅用于实盘风控，不计入 Sharpe |
| DD control | ⚠️ | 同上，实盘保护用，不计入 Sharpe |
| 统计审计 | ✅ | Newey-West, FDR, VIF, WFCV 全部通过 |
| 多重检验 | ✅ | BH-FDR 校正后 GPA/volatility 显著 |
| Walk-Forward | ✅ | 月频 decay 25%, 日频 decay 11% |

### 已修正的 bias

| Bias | 之前 | 修正后 |
|------|------|--------|
| Sharpe 虚高 | 2.06 (vol managed) | **0.97** (raw) |
| 日频 lookahead | 无 shift, Sharpe 20+ | **1.48** (shift(1)) |
| 多重检验 | 31 factors 无校正 | BH-FDR, 仅 2 通过 |
| VIF | volatility/downside_vol VIF 65 | 清理后 < 10 |
| 日频因子方向 | IC sign 翻转 | 保持原始方向 |
