# 变更：增强新闻情绪解析

## 为什么

当前 `fetch_news_alphavantage()` 函数存在两个数据利用不足的问题：

1. **个股情绪丢失**：只抓取 `overall_sentiment_score`（整体情绪），忽略了 `ticker_sentiment` 字段。一篇对比文章可能对 NVDA 利好但对 INTC 利空，仅看整体情绪会丢失关键对冲信息。

2. **话题标签缺失**：忽略了 `topics` 字段。API 会自动为新闻打标（如 earnings、mergers_and_acquisitions），并附带相关度分数，有助于筛选"硬核"新闻。

## 变更内容

### 1. 个股专属情绪 (Ticker-Specific Sentiment)
- 解析 API 返回的 `ticker_sentiment` 字段
- 新增 `ticker_sentiment_score` 和 `ticker_sentiment_label` 列
- 当查询特定 ticker 时，优先提取该股票的专属情绪

### 2. 话题标签 (Topic Tagging)
- 解析 API 返回的 `topics` 字段
- 新增 `topics` 列，包含话题名称和相关度分数

### 文件变更

| 类型 | 文件 |
|------|------|
| MODIFY | `.agent/skills/finance-data-news/scripts/fetch_news.py` |
| MODIFY | `.agent/skills/finance-data-news/SKILL.md` |

## 影响

- 受影响规范：`news-sentiment-data`（新增）
- 受影响代码：`fetch_news_alphavantage()` 函数
- 外部依赖：无新增

> [!NOTE]
> 此变更不会破坏现有接口，仅在返回的 DataFrame 中新增列。
