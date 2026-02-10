# 规范：Alpha Intelligence 数据获取

本规范定义了通过 Alpha Vantage Alpha Intelligence™ API 获取高级市场洞察数据的能力。

## 新增需求

### 需求：获取财报电话会议记录

系统**必须**支持获取指定公司特定季度的财报电话会议完整记录。返回数据**必须**包含会议记录文本、LLM情绪分析、季度标识和股票代码。

#### 场景：查询 IBM 2024年第一季度财报会议

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_earnings_call(symbol="IBM", quarter="2024Q1")`  
**那么** 系统返回包含 `transcript`、`sentiment`、`quarter`、`symbol` 字段的 DataFrame

---

### 需求：获取美股涨跌幅排行

系统**必须**支持获取美股当日涨幅、跌幅、成交量前20名股票。返回数据**必须**包含涨幅榜、跌幅榜和成交量榜三个列表。

#### 场景：获取当日市场排行榜

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_top_movers()`  
**那么** 系统返回包含 `gainers`、`losers`、`most_actively_traded` 三个键的字典

---

### 需求：获取内部人士交易记录

系统**必须**支持获取指定公司关键利益相关者的最新及历史交易记录。返回数据**必须**包含交易日期、内部人姓名、职位、交易类型、股数和交易金额。

#### 场景：查询 IBM 的内部人交易

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_insider_transactions(symbol="IBM")`  
**那么** 系统返回包含交易详情的 DataFrame

---

### 需求：新闻时间范围筛选

系统**必须**支持在新闻查询中指定时间范围和排序方式。时间格式**必须**为 `YYYYMMDDTHHMM`。

#### 场景：查询特定时间段的科技新闻

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_news(query_type="sector", keyword="technology", time_from="20240101T0000", time_to="20240131T2359")`  
**那么** 系统返回2024年1月内的科技板块新闻

#### 场景：按相关性排序新闻

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_news(query_type="ticker", ticker="AAPL", sort="RELEVANCE")`  
**那么** 系统返回按相关性排序的 AAPL 相关新闻
