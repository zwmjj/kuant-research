# statistical Capital 策略检查 — 完整 Checklist

基于12道 Scenario Questions 的核心框架

---

## Section 1：Statistical Inference & Multiple Testing

### 多重检验
- [ ] 测试了多少个信号/策略？期望 false positive 数量 = N × 0.05
- [ ] 是否用 Bonferroni（t-stat > 3.9）或 BH-FDR 或 Harvey Liu Zhu（t-stat > 3.0）调整 threshold
- [ ] 计算 DSR — 试了N个策略后，SR* ≈ 2.0-2.5，DSR 是否 > 0.5

### IC 显著性
- [ ] ICIR = IC_mean / IC_std（目标 > 0.5）
- [ ] t-stat = ICIR × √N（目标 > 3.0）
- [ ] IC 是否有 autocorrelation？用 ACF 检验，如有则用 N_eff = N × (1-ρ)/(1+ρ) 调整 t-stat
- [ ] 调整后 t-stat 仍然 > 2.0？用 Newey-West 做正式推断

### Fundamental Law
- [ ] IR ≈ IC × √Breadth（Breadth = 股票数 × 换仓频率/年）
- [ ] 目标 IR 是否达标？

---

## Section 2：Data Integrity

### 数据质量
- [ ] 数据源是否可靠？
- [ ] NaN/缺失数据如何处理？cross-sectional filling 还是 discard？
- [ ] Outlier 处理 — returns > 50%/天是否是 data error？winsorise at 3 sigma？

### 三种 Bias
- [ ] Lookahead bias：所有数据是否 PIT 对齐？在交易时刻真实可得？
- [ ] Survivorship bias：universe 是否包含所有历史上存在的股票，包括退市的？
- [ ] Selection/Overfitting bias：这是 N 次尝试里最好的结果吗？计算 DSR

### Factor 构建
- [ ] Cross-sectional 标准化（z-score within each date）
- [ ] Beta 和 size neutralization — 确保 attribution 清晰，没有意外 factor exposure
- [ ] Universe 定义是否合理（流动性筛选，小股票是否适合策略）

---

## Section 3：Backtest Framework

### OOS 设计
- [ ] 是否有真正封存的 holdout period，在开发过程中从未被看过？
- [ ] Walk-forward CV：Rolling window（alpha 信号首选，避免旧数据污染）还是 Expanding window？
- [ ] 训练集长度：日度数据至少 2-3 年（500-750 个观测），月度数据至少 5 年（60 个观测）
- [ ] Feature selection 是否在每个训练窗口内独立进行？（不能在全数据上先选再 split）
- [ ] λ（regularisation 参数）是否在训练集内用 CV 选定？（不能用测试集）

### 过拟合检查
- [ ] 观测数 / feature 数 ≥ 10（理想 20）
- [ ] 如果 < 10：用 Domain knowledge 减少 feature，VIF 检测后用 Lasso 或 Elastic Net
- [ ] IS vs OOS Sharpe decay：日内高频 < 20-30%，低频月度 < 40%
- [ ] Sharpe retention threshold：高频 70-80%，低频 60%

---

## Section 4：Statistical Diagnostics

### 回归诊断
- [ ] Residual autocorrelation：画 ACF，Durbin-Watson（DW < 2 为正 autocorrelation），Ljung-Box
- [ ] 如有 autocorrelation：用 Newey-West HAC SE（m = T^(1/3)），检查是否有遗漏 factor
- [ ] Multicollinearity：VIF = 1/(1-R²_j)，VIF > 5 需要关注，> 10 严重
- [ ] 如有 multicollinearity：Drop（IC低/turnover高/intuition弱的）、正交化、PCA、Elastic Net

### 时间序列
- [ ] IC 时间序列是否稳定？rolling 12 个月 IC 均值是否有系统性下降趋势？
- [ ] IC 在不同 regime 下（VIX < 20，20-30，> 30）是否 consistent？
- [ ] Correlation 是否稳定？用 rolling 60天/EWMA（λ=0.94-0.97）检测 structural change
- [ ] 如 correlation 变化：更新 risk model，做 stress test（correlation 回到历史高点）

---

## Section 5：Live Performance Diagnosis

### 统计检验
- [ ] t-stat = SR × √T（检验是否显著异于 0）
- [ ] t-stat = (SR_obs - SR_backtest) / (1/√T)（检验是否显著低于 backtest 水平）
- [ ] 15 个月数据：t-stat ≈ 0.34（不显著异于 0），但可以拒绝 SR = 2.0（t ≈ -1.9）

### 诊断顺序
1. **回测本身是否可信？** 数据质量、PIT、bias、OOS 设计、DSR
2. **市场变了吗？** Regime change（rolling Sharpe 突然断崖 vs 逐渐衰减）、Signal decay（IC 时间序列下降）、Crowding（同类策略 AUM、13F 持仓集中度）
3. **执行出问题了吗？** Slippage vs backtest 假设、Market impact（ADV 占比）、TCA 建模

### Regime 处理
- [ ] Vol targeting：leverage = σ_target / σ_realized（首选，不需要 calibrate threshold）
- [ ] Regime filter：VIX threshold 用 WFCV 选，Sigmoid 平滑避免频繁开关
- [ ] Stress test：VIX 20/25/30/35 敏感性分析，避免 overfit 单一 threshold

---

## Section 6：Portfolio Integration

### 加入组合前
- [ ] 与现有因子/策略的 correlation < 80%（高于则检查独立 contribution）
- [ ] VIF 检测 multicollinearity
- [ ] 如高度相关：Drop（IC低/turnover高）、正交化（regress 弱 factor on 强 factor，用残差）、PCA（多因子高度相关时）
- [ ] Factor exposure 方向是否符合预期？Beta/size/sector exposure 是否 neutralized？
- [ ] 边际风险贡献是否合理？

### Capacity 评估
- [ ] 目标 AUM < 10-15% ADV
- [ ] 高 AUM 下 market impact 是否会消灭 alpha？

---

## Section 7：部署流程

- [ ] 独立工程师复现结果（相同 Sharpe）
- [ ] 风控团队审核
- [ ] 投资委审批
- [ ] Paper trading 6 个月，严格 TC/slippage/market impact 假设
- [ ] Sharpe retention 达标后才进入小盘实盘
- [ ] 预先设定 drawdown limit 和 performance review trigger

---

## 关键数字速查

| 参数 | 数值 |
|---|---|
| HLZ t-stat threshold | > 3.0 |
| Bonferroni（500个信号） | t-stat > 3.9 |
| DSR acceptable | > 0.5，理想 > 0.95 |
| ICIR decent | > 0.5 |
| Obs per feature rule of thumb | 10-20x |
| EWMA λ（日度） | 0.94（11天）/ 0.97（23天） |
| Newey-West lag m | T^(1/3) |
| N_eff 公式 | N × (1-ρ)/(1+ρ) |
| VIF threshold | > 5 关注，> 10 严重 |
| Sharpe retention（高频） | 70-80% |
| Sharpe retention（低频） | 60% |
| Capacity rule of thumb | < 10-15% ADV |
| Paper trading 期限 | 6 个月 |
