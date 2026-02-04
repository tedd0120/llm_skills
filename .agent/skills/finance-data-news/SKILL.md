---
description: 抓取时事热点新闻，支持全球宏观、板块关键词、个股新闻
---

# 新闻数据抓取 Skill

使用 akshare 和 Alpha Vantage 抓取金融市场相关新闻。

## 功能

1. **全球宏观新闻** - 获取宏观经济、金融市场相关新闻
2. **板块关键词新闻** - 按行业板块筛选新闻
3. **个股新闻** - 获取特定股票相关新闻

## 数据源

| 数据源 | 适用场景 | 特点 |
|--------|----------|------|
| akshare | A股个股新闻 | 无调用限制 |
| Alpha Vantage | 全球新闻、板块新闻 | 包含情绪分析，每日25次免费额度 |

## 使用方法

### 获取全球宏观新闻

```python
from scripts.fetch_news import fetch_news

# 获取全球宏观经济新闻
df = fetch_news(query_type="global", limit=20)
print(df[["title", "sentiment_score"]])
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

## 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| query_type | str | 查询类型: `"global"` / `"sector"` / `"ticker"` |
| keyword | str | 板块关键词（query_type="sector"时使用） |
| ticker | str | 股票代码（query_type="ticker"时使用） |
| source | str | 数据源: `"auto"` / `"akshare"` / `"alphavantage"` |
| limit | int | 返回条数限制，默认50 |

## 输出格式

DataFrame 包含以下列：
- `title` - 新闻标题
- `summary` - 内容摘要
- `source` - 来源
- `url` - 原文链接
- `published_time` - 发布时间
- `sentiment_score` - 情绪分数（仅Alpha Vantage）
- `tickers` - 关联股票代码

## 注意事项

> ⚠️ Alpha Vantage 免费账户每日仅 25 次 API 调用，请合理使用。
