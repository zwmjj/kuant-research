# Kuant 数据源指南

## 当前已接入

| 数据源 | 市场 | 内容 | 费用 | 状态 |
|--------|------|------|------|------|
| **WRDS/CRSP** | 美股 | 月频价格/收益/退市/成交量 | 学校账号免费 | ✅ 运行中 |
| **WRDS/Compustat** | 美股 | 年报基本面(ROE/BM/GP等) | 同上 | ✅ 运行中 |
| **WRDS/FF** | 美股 | Fama-French因子 | 同上 | ✅ 运行中 |
| **baostock** | A股 | 月频后复权/成交量/换手率 | **免费** | ✅ 运行中 |
| **akshare** | A股 | 指数日线(CSI300等) | **免费** | ⚠ 个股限流 |
| **yfinance** | 美股 | SPY基准补充 | **免费** | ✅ 补充用 |

---

## 免费数据源

### 美股

| 数据源 | 内容 | 频率 | 质量 | 接入难度 | 备注 |
|--------|------|------|------|----------|------|
| **Kenneth French Library** | FF3/5因子、行业分组 | 月 | ★★★★★ | 低 | pandas_datareader直接拉 |
| **FRED (St. Louis Fed)** | 宏观指标(利率/GDP/CPI/VIX) | 日/月 | ★★★★★ | 低 | `fredapi`包, 免费API key |
| **SEC EDGAR** | 10-K/10-Q全文, 内部交易 | 事件 | ★★★★ | 中 | XML解析, 免费API |
| **Yahoo Finance** | 价格/成交量/基本面 | 日 | ★★★ | 低 | `yfinance`, 不稳定 |
| **Alpha Vantage** | 价格/基本面/经济指标 | 日 | ★★★ | 低 | 免费500次/天 |
| **Tiingo** | EOD价格、新闻 | 日 | ★★★★ | 低 | 免费500次/小时 |
| **Polygon.io** | 价格/期权/新闻 | 分钟 | ★★★★ | 低 | 免费tier 5次/分钟 |
| **OpenBB** | 聚合多源(整合了上面很多) | 混合 | ★★★★ | 中 | Python SDK, 免费 |

### A股

| 数据源 | 内容 | 频率 | 质量 | 接入难度 | 备注 |
|--------|------|------|------|----------|------|
| **baostock** | 价格/财务/成分股 | 日/月 | ★★★★ | **低** | 完全免费无限量 |
| **akshare** | 几乎所有A股数据 | 日 | ★★★★ | 低 | 免费但有限流 |
| **Tushare** | 价格/财务/分析师/龙虎榜 | 日 | ★★★★★ | 低 | 免费200积分/天, 高级要付费 |
| **efinance** | 实时行情/历史数据 | 分钟 | ★★★ | 低 | 完全免费 |
| **CSMAR (国泰安)** | 学术级A股全量 | 日/月 | ★★★★★ | 高 | 学校账号免费 |
| **Wind万得** | 最全A股数据 | tick | ★★★★★ | 中 | 个人¥0(学校), 机构很贵 |

### 另类数据 (免费)

| 数据源 | 内容 | 用途 | 接入 |
|--------|------|------|------|
| **GDELT** | 全球新闻事件 | 情绪因子 | BigQuery免费 |
| **Reddit/Twitter API** | 社交媒体情绪 | 散户情绪 | 免费tier |
| **Google Trends** | 搜索热度 | 注意力因子 | `pytrends` |
| **NOAA** | 天气数据 | 农业/能源 | 免费API |

---

## 低成本数据源 ($10-100/月)

### 美股

| 数据源 | 内容 | 费用 | 亮点 |
|--------|------|------|------|
| **Polygon.io Starter** | 全美股日频+延迟分钟 | $29/月 | REST+WebSocket, 好用 |
| **Tiingo Pro** | 价格+IEX实时+基本面 | $10/月 | 最便宜的实时数据 |
| **Alpha Vantage Premium** | 不限次调用 | $50/月 | 简单API |
| **Quandl/Nasdaq Data Link** | 机构级因子数据 | $50/月起 | Sharadar基本面 |
| **EOD Historical Data** | 全球70+交易所 | $20/月 | 覆盖面最广 |
| **Alpaca Markets** | 实时美股+纸交易 | **免费** | 最佳模拟盘选择 |
| **IEX Cloud** | 价格/基本面/另类 | $9/月起 | 质量好 |

### A股

| 数据源 | 内容 | 费用 | 亮点 |
|--------|------|------|------|
| **Tushare Pro** | 全量A股+港股 | ¥500/年(~$70) | 最佳性价比 |
| **RiceQuant 米筐** | 全量+回测平台 | ¥2000/年 | 含回测 |
| **JoinQuant 聚宽** | 全量+研究平台 | 免费(限制)+¥99/月 | 在线notebook |

---

## 专业级 ($100+/月)

| 数据源 | 内容 | 费用 | 适合 |
|--------|------|------|------|
| **Bloomberg Terminal** | 万物 | $2000/月 | 机构标配 |
| **Refinitiv Eikon** | 万物 | $300/月起 | Bloomberg替代 |
| **FactSet** | 基本面+另类 | $1000/月 | 买方分析 |
| **S&P Capital IQ** | 基本面深度 | $500/月 | 公司分析 |
| **WRDS** | 学术数据库集合 | 学校免费/个人$500/年 | 你已经有 |
| **OptionMetrics (via WRDS)** | 期权隐含波动率面 | 学校免费 | vol策略必备 |

---

## 推荐接入优先级

### Phase 1: 立即可做 (免费, 0成本)

1. **FRED宏观数据** → regime因子(利率曲线/VIX/信用利差)
   ```python
   pip install fredapi
   # 需要免费API key: https://fred.stlouisfed.org/docs/api/api_key.html
   ```

2. **Kenneth French Data** → 更多因子(行业动量/质量因子等)
   ```python
   import pandas_datareader.data as web
   ff = web.DataReader('F-F_Research_Data_5_Factors_2x3', 'famafrench')
   ```

3. **SEC EDGAR** → 10-K文本分析, 内部交易
   ```python
   # 免费API: https://www.sec.gov/edgar/sec-api-documentation
   ```

4. **Tushare基础版** → A股财务数据(ROE/BM等), 补全个股基本面
   ```python
   pip install tushare
   # 免费注册: https://tushare.pro/register
   ```

5. **baostock财务报表** → A股季报数据(已安装)
   ```python
   bs.query_profit_data()  # 盈利能力
   bs.query_operation_data()  # 运营能力
   bs.query_growth_data()  # 成长能力
   ```

### Phase 2: 小投入大价值 ($10-50/月)

6. **Polygon.io Starter ($29/月)** → 美股日内数据, 改善执行模型
7. **Tushare Pro (¥500/年)** → A股全量, 解锁更多A股因子
8. **Alpaca Paper Trading (免费)** → 真实模拟盘, 验证策略

### Phase 3: 深度研究

9. **OptionMetrics (via WRDS)** → 隐含波动率面, vol策略升级
10. **IBES (via WRDS)** → 分析师预期, SUE/PEAD因子
11. **CRSP Daily (via WRDS)** → 日频数据, 精确执行模型

---

## 数据质量对策略的影响

| 数据缺陷 | 当前影响 | 解决方案 |
|----------|---------|----------|
| A股无历史成分股调整 | 幸存者偏差~2% | Tushare Pro有历史成分股 |
| A股无基本面(ROE/BM) | 无法做价值/质量因子 | baostock财报+Tushare |
| 美股无日频数据 | 执行模型粗糙 | Polygon/CRSP Daily |
| 无隐含波动率 | vol因子只用实现波动率 | OptionMetrics |
| 无分析师预期 | 无SUE/PEAD | IBES via WRDS |
| 无涨跌停数据 | A股执行偏差 | baostock日频有涨跌停标记 |
