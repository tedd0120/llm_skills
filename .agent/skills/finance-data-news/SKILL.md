---
description: 抓取时事热点新闻，支持全球宏观、板块关键词、个股新闻，以及财报会议、涨跌幅排行和内部人交易
---

# 新闻与市场洞察 Skill

使用 akshare 和 Alpha Vantage 抓取金融市场相关新闻及高级市场洞察数据。

## 功能

### 基础功能
1. **全球宏观新闻** - 获取宏观经济、金融市场相关新闻
2. **板块关键词新闻** - 按行业板块筛选新闻
3. **个股新闻** - 获取特定股票相关新闻

### Alpha Intelligence™ 高级功能
4. **涨跌幅排行榜** - 美股当日涨/跌/成交量 Top 20
5. **内部人交易记录** - 追踪公司高管、董事等关键人物买卖行为

## 数据源

| 数据源 | 适用场景 | 特点 |
|--------|----------|------|
| akshare | A股个股新闻 | 无调用限制 |
| Alpha Vantage | 全球新闻、高级洞察 | 包含情绪分析，每日25次免费额度 |

## 使用方法

### 获取全球宏观新闻

```python
from scripts.fetch_news import fetch_news

# 获取全球宏观经济新闻
df = fetch_news(query_type="global", limit=20)
print(df[["title", "sentiment_score"]])

# 按相关性排序，筛选特定时间段
df = fetch_news(
    query_type="global",
    time_from="20240101T0000",
    time_to="20240131T2359",
    sort="RELEVANCE"
)
```

### 获取板块新闻

```python
from scripts.fetch_news import fetch_news

# 获取科技板块新闻
df = fetch_news(query_type="sector", keyword="technology")

# 支持的关键词：technology, blockchain, earnings, ipo, 
# mergers_and_acquisitions, financial_markets, economy_fiscal,
# economy_monetary, economy_macro, energy_transportation,
# life_sciences, manufacturing, real_estate, retail_wholesale, finance
```

### 获取个股新闻

```python
from scripts.fetch_news import fetch_news

# A股个股（自动使用akshare）
df = fetch_news(query_type="ticker", ticker="000001")

# 美股个股（自动使用Alpha Vantage）
df = fetch_news(query_type="ticker", ticker="AAPL")
```


### 获取涨跌幅排行榜

```python
from scripts.fetch_news import fetch_top_movers

# 获取美股当日涨跌幅排行
result = fetch_top_movers()
print("涨幅榜:", result["gainers"][["ticker", "change_percentage"]].head())
print("跌幅榜:", result["losers"][["ticker", "change_percentage"]].head())
print("成交量榜:", result["most_actively_traded"][["ticker", "volume"]].head())
```

### 获取内部人交易记录

```python
from scripts.fetch_news import fetch_insider_transactions

# 获取 IBM 内部人交易记录
df = fetch_insider_transactions(symbol="IBM")
print(df[["transaction_date", "insider_name", "transaction_type", "shares"]])
```

## 参数说明

### fetch_news() 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| query_type | str | 查询类型: `"global"` / `"sector"` / `"ticker"` |
| keyword | str | 板块关键词（query_type="sector"时使用） |
| ticker | str | 股票代码（query_type="ticker"时使用） |
| source | str | 数据源: `"auto"` / `"akshare"` / `"alphavantage"` |
| limit | int | 返回条数限制，默认50 |
| time_from | str | 开始时间，格式 `YYYYMMDDTHHMM`（仅Alpha Vantage） |
| time_to | str | 结束时间，格式 `YYYYMMDDTHHMM`（仅Alpha Vantage） |
| sort | str | 排序方式: `"LATEST"` / `"EARLIEST"` / `"RELEVANCE"` |


### fetch_insider_transactions() 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| symbol | str | 股票代码，如 `"IBM"` |

## 输出格式

### 新闻 DataFrame
- `title` - 新闻标题
- `summary` - 内容摘要
- `source` - 来源
- `url` - 原文链接
- `published_time` - 发布时间
- `sentiment_score` - 文章整体情绪分数（仅Alpha Vantage）
- `sentiment_label` - 文章整体情绪标签
- `tickers` - 关联股票代码列表
- `ticker_sentiments` - 各股票专属情绪（JSON格式）
- `topics` - 话题标签，格式 "topic1:score,topic2:score"
- `target_ticker_sentiment` - 查询股票的专属情绪分数（仅ticker查询时有值）
- `target_ticker_label` - 查询股票的情绪标签（如Bullish/Bearish）


### 内部人交易 DataFrame
- `transaction_date` - 交易日期
- `insider_name` - 内部人姓名
- `insider_title` - 职位
- `transaction_type` - 买入/卖出
- `shares` - 股数
- `value` - 交易金额

## 注意事项

> ⚠️ Alpha Vantage 免费账户每日仅 25 次 API 调用，请合理使用。
> - 优先使用 akshare 获取 A股数据
> - 财报会议记录文本较长，注意处理
> - 涨跌幅数据在收盘后更新（非实时）
