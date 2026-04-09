# statistical Strategy Audit — 现有策略检查结果

**审计日期**: 2026-04-04
**审计范围**: quant/ 全平台（qf/ 核心框架 + 25+ 策略 + 实盘基础设施）
**主要策略**: regime_blend (Sharpe 1.19, OOS 1.08)

---

## Section 1：Statistical Inference & Multiple Testing

### 多重检验

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 测试了多少个信号/策略 | ⚠️ 已知但未调整 | 31+ factors, 25+ strategies, 期望 false positive ≈ 1.5 个 |
| Bonferroni / BH-FDR / HLZ 调整 | ❌ **缺失** | 无任何多重检验校正，所有 t-stat 均为未调整值 |
| DSR 计算 | ✅ 已实现 | risk.py 实现了 Bailey & Lopez de Prado (2014)，gate check 要求 DSR > 95% |
| DSR 参数 n_trials | ⚠️ 默认20 | 实际测试了 25+ 策略，n_trials 应调高到真实数量 |

**🔴 关键缺口**: 没有 Bonferroni/FDR 校正。测了 31 个 factor，至少 1-2 个会偶然显著。需要实现 `statsmodels.stats.multitest.multipletests(method='fdr_bh')` 并重新筛选。

### IC 显著性

| 检查项 | 状态 | 详情 |
|--------|------|------|
| ICIR 计算 | ✅ 已实现 | factor_analysis.py: IR = mean(IC) / std(IC) |
| t-stat = ICIR × √N | ⚠️ 部分 | 计算了 IR 但未显式报告 t-stat |
| IC autocorrelation 检验 | ❌ **缺失** | 无 ACF/Ljung-Box 检验 |
| N_eff 调整 | ❌ **缺失** | 无 N_eff = N × (1-ρ)/(1+ρ) 公式 |
| Newey-West 推断 | ❌ **缺失** | 所有 t-stat 假设独立观测，可能严重膨胀 |

**🔴 关键缺口**: IC 的 autocorrelation 未检验，t-stat 可能虚高 2-3 倍。月度 factor IC 通常有显著 autocorrelation。

### Fundamental Law

| 检查项 | 状态 | 详情 |
|--------|------|------|
| IR ≈ IC × √Breadth | ❌ **缺失** | 未显式计算 Fundamental Law 分解 |

---

## Section 2：Data Integrity

### 数据质量

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 数据源可靠性 | ✅ **优秀** | WRDS CRSP/Compustat（机构级），yfinance 补充 |
| NaN 处理 | ✅ 已实现 | completeness > 60% 过滤 + forward-fill |
| Outlier 处理 | ⚠️ 部分 | 信号层面有 winsorize at 1%/99%，但 returns 层面未见 3σ winsorize |

### 三种 Bias

| 检查项 | 状态 | 详情 |
|--------|------|------|
| Lookahead bias | ✅ **优秀** | shift(1) 全面应用，Fama-French 6 个月 lag，Phase 4 审计通过 |
| Survivorship bias | ✅ **优秀** | Shumway (1997) 方法，8,446 条退市记录，performance delist 默认 -30% |
| Selection/Overfitting bias | ⚠️ 部分 | DSR 已实现但 n_trials 参数偏低；缺多重检验校正 |

### Factor 构建

| 检查项 | 状态 | 详情 |
|--------|------|------|
| Cross-sectional 标准化 | ⚠️ 用 rank 代替 z-score | cross_sectional_rank() 映射到 [-1,1]，但不是标准 z-score |
| Beta/size neutralization | ⚠️ 部分 | 仅 orthogonal signals 做了回归残差，非系统性全覆盖 |
| Universe 定义 | ✅ 合理 | 价格 > $5，top 25% 市值，completeness > 60% |

---

## Section 3：Backtest Framework

### OOS 设计

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 封存的 holdout period | ⚠️ 部分 | 有 70/30 time-series split（FactorSelector），但非独立封存 |
| Walk-forward CV | ⚠️ **独立未集成** | walk_forward_cv.py 存在但未接入主 backtest 循环 |
| 训练集长度 | ✅ 充足 | 2010-2024 共 15 年月度数据（180 个观测） |
| Feature selection 独立 | ⚠️ 不确定 | FactorSelector 用 70/30 split，但不是每个 window 独立选 |
| λ 在训练集内 CV | ⚠️ 部分 | LightGBM 有 early stopping，但 regularisation 未见显式 CV |

**🟡 重要缺口**: Walk-forward CV 存在但未集成到主回测。当前回测本质上是全样本回测 + 信号 lag。

### 过拟合检查

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 观测/feature 比 ≥ 10 | ✅ | 180 月 / 5-10 features = 18-36x |
| IS vs OOS Sharpe decay | ✅ **优秀** | regime_blend: IS 1.22 → OOS 1.08 = 11% decay（远优于 40% 阈值）|
| Sharpe retention | ✅ | 1.08/1.22 = 88.5%（超过 60% 低频阈值）|

---

## Section 4：Statistical Diagnostics

### 回归诊断

| 检查项 | 状态 | 详情 |
|--------|------|------|
| Residual ACF / Durbin-Watson | ❌ **缺失** | 无 autocorrelation 诊断 |
| Newey-West HAC SE | ❌ **缺失** | 所有推断假设 i.i.d.，月度数据几乎必有 autocorrelation |
| VIF multicollinearity | ❌ **缺失** | 31 个 factor 无 VIF 检查 |
| 高 VIF 处理 | N/A | 未检测无法处理 |

**🔴 关键缺口**: Newey-West 和 VIF 完全缺失。这是 statistical 面试中最可能被挑战的点。

### 时间序列

| 检查项 | 状态 | 详情 |
|--------|------|------|
| Rolling IC 稳定性 | ⚠️ 部分 | IC decay analysis 存在（多 lag），但无 rolling 12 月均值趋势 |
| Regime 条件 IC | ❌ **缺失** | 未按 VIX regime 分组检查 IC consistency |
| Rolling correlation / EWMA | ⚠️ 部分 | anomaly_detector 有 CUSUM，但无 EWMA correlation 监控 |
| Structural change 检测 | ⚠️ 部分 | CUSUM 存在但非专门针对 factor correlation |

---

## Section 5：Live Performance Diagnosis

### 统计检验

| 检查项 | 状态 | 详情 |
|--------|------|------|
| t-stat = SR × √T | ⚠️ 未显式报告 | paper trading 8 个月: t = 2.15 × √(8/12) ≈ 1.76（不显著）|
| IS vs live 显著性差异 | ❌ 未做 | 未计算 (SR_obs - SR_backtest) / (1/√T) |

### 诊断顺序

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 回测可信度 | ✅ | Phase 3/4 审计通过，bias 处理良好 |
| 市场变化检测 | ⚠️ 部分 | anomaly_detector 有，但无 rolling Sharpe 断崖分析 |
| 执行问题检测 | ⚠️ 部分 | TCA 存在（5 个 cost model），但无 partial fill / slippage 对比 |

### Regime 处理

| 检查项 | 状态 | 详情 |
|--------|------|------|
| Vol targeting | ✅ 已实现 | σ_target / σ_realized，max leverage 1.5x |
| Regime filter | ⚠️ 硬阈值 | VIX threshold 用固定 mean+1σ，无 sigmoid 平滑，无 WFCV |
| Stress test 敏感性 | ⚠️ 部分 | 10 个历史危机 replay，但无 VIX 20/25/30/35 参数扫描 |

---

## Section 6：Portfolio Integration

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 策略间 correlation | ❌ **缺失** | 25+ 策略无相互 correlation matrix |
| VIF 检测 | ❌ **缺失** | 同上 |
| Factor exposure 验证 | ⚠️ 部分 | FF5 attribution 存在，但非所有策略都跑过 |
| 边际风险贡献 | ❌ **缺失** | 无 marginal risk contribution 计算 |
| Capacity 评估 | ⚠️ 部分 | ADV floor $10K，participation rate 有上限，但无 AUM scaling |
| AUM < 10-15% ADV | ⚠️ 未显式检查 | cost model 有 participation rate 但无 capacity ceiling |

---

## Section 7：部署流程

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 独立复现 | ⚠️ Phase 4 审计算部分 | 内部审计通过，但非独立第三方 |
| 风控审核 | ✅ 4 层风控 | position/exposure/loss/trade count 限制 |
| Paper trading 6 个月 | ⚠️ 模拟 8 个月 | paper_trading.py 跑了 8 个月模拟，但是 simulated 非真实 paper |
| Drawdown limit 设定 | ✅ 已设 | 10%/20%/25% 三级减仓 |

---

## 总结评分

| Section | 评分 | 关键问题 |
|---------|------|----------|
| 1. Statistical Inference | 🔴 D+ | 缺 Bonferroni/FDR，缺 Newey-West，DSR n_trials 偏低 |
| 2. Data Integrity | ✅ A | 优秀的 survivorship + PIT + data quality |
| 3. Backtest Framework | 🟡 B | OOS decay 优秀但 walk-forward 未集成 |
| 4. Statistical Diagnostics | 🔴 D | 缺 ACF/DW/Newey-West/VIF，核心诊断全缺 |
| 5. Live Diagnosis | 🟡 C+ | Vol targeting 好，regime 处理硬阈值 |
| 6. Portfolio Integration | 🔴 D | 缺 correlation matrix，缺 marginal risk，缺 capacity |
| 7. 部署流程 | 🟡 B- | 基础设施完整，但未真正 paper trade 6 个月 |

---

## ✅ 已修复 — Priority 1 (2026-04-04)

### 1. ✅ Newey-West HAC Standard Errors
- **位置**: `qf/factor_analysis.py::ic_tstat_newey_west()`
- **实现**: OLS + HAC cov, lag m = T^(1/3)
- **实测结果**: 本数据集 IC 有轻微负 autocorrelation，NW t-stat 反而略大于 naive（好消息）

### 2. ✅ Multiple Testing Correction (BH-FDR)
- **位置**: `qf/factor_analysis.py::multiple_testing_correction()`
- **实现**: Bonferroni / BH-FDR / Holm，via `statsmodels.stats.multitest.multipletests`
- **实测结果**: 11 factors 中，校正前 4 个显著 → 校正后仅 2 个（max_return, volatility）

### 3. ✅ VIF Multicollinearity Check
- **位置**: `qf/factor_analysis.py::compute_vif()`
- **实现**: `variance_inflation_factor` + 手动 fallback
- **实测结果**: volatility VIF=65, downside_vol=38, max_return=28（严重共线性）

### 4. ✅ IC Autocorrelation Test + N_eff
- **位置**: `qf/factor_analysis.py::ic_autocorrelation_test()`
- **实现**: Ljung-Box test + N_eff = N × (1-ρ)/(1+ρ)
- **一键审计**: `full_statistical_audit()` 组合以上四项

## ✅ 已修复 — Priority 2 (2026-04-04)

### 5. ✅ Walk-Forward CV
- **位置**: `qf/gsa_toolkit.py::WalkForwardCV`
- **实现**: Rolling/expanding window, 逐 fold 计算 IS/OOS Sharpe + decay
- **实测结果**: 7 folds, avg IS=0.84, avg OOS=0.81, decay=4.2%

### 6. ✅ Cross-Sectional Z-Score
- **位置**: `qf/signals.py::SignalGenerator.cross_sectional_zscore()` + `qf/gsa_toolkit.py::cross_sectional_zscore()`
- **实现**: z-score with winsorize at ±3σ，保留 magnitude 信息
- **实测结果**: IC 与 rank 版几乎一致（Spearman IC 不受 monotone transform 影响）

### 7. ✅ Regime-Conditional IC Analysis
- **位置**: `qf/gsa_toolkit.py::regime_conditional_ic()`
- **实现**: 按 VIX/vol regime 分组计算 IC, t-stat, p-value
- **实测结果**: max_return 在 low VIX 时 IC=0.09 (t=2.87, p=0.004)，high VIX 时 IC=0.01 (ns) — alpha 主要来自低波环境

### 8. ✅ Strategy Correlation Matrix + Marginal Risk
- **位置**: `qf/gsa_toolkit.py::strategy_correlation_matrix()` + `marginal_risk_contribution()`
- **实现**: Pairwise correlation + MCTR (marginal contribution to risk)
- **实测结果**: volatility/max_return 相关 0.83（需处理），momentum 与 vol 类低相关

### 9. ✅ Capacity Ceiling 估算
- **位置**: `qf/gsa_toolkit.py::estimate_capacity()`
- **实现**: AUM vs participation rate vs sqrt impact curve
- **实测结果**: 大盘股策略容量 ~$3B（10% ADV 限制），但 impact 在 $50M+ 显著

### 10. ✅ Sigmoid Regime Filter
- **位置**: `qf/gsa_toolkit.py::sigmoid_regime_weight()` + `calibrate_sigmoid_wfcv()`
- **位置**: `qf/optimizer.py::sigmoid_regime_scale()`
- **实现**: weight = min_w + (1-min_w)/(1+exp(k*(VIX-center)))，WFCV 校准参数
- **实测结果**: VIX=12 → 98% exposure, VIX=25 → 60%, VIX=40 → 21%

### Bonus: Factor Orthogonalization
- **位置**: `qf/gsa_toolkit.py::orthogonalize_factors()`
- **实现**: 对高 VIF 因子做 cross-sectional regression residual
- **实测结果**: vol_of_vol_orth VIF 降至 1.1，但 volatility/downside_vol 残差仍高度相关

### Bonus: Fundamental Law of Active Management
- **位置**: `qf/gsa_toolkit.py::fundamental_law_decomposition()`
- **实现**: IR ≈ IC × √Breadth，Transfer Coefficient 计算
- **实测结果**: max_return IC=0.08, predicted IR=1.56, actual IR=0.30, TC=0.19
