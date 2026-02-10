# 设计文档：增强新闻情绪解析

## 上下文

Alpha Vantage NEWS_SENTIMENT API 返回的每篇新闻包含：
- `overall_sentiment_score` - 文章整体情绪分数
- `overall_sentiment_label` - 文章整体情绪标签
- `ticker_sentiment` - 每个相关股票的专属情绪
- `topics` - 文章话题标签及相关度

当前实现仅使用 `overall_sentiment_score`，丢失了个股维度的情绪数据和话题信息。

## API 返回示例

```json
{
  "ticker_sentiment": [
    {
      "ticker": "NVDA",
      "relevance_score": "0.9",
      "ticker_sentiment_score": "0.35",
      "ticker_sentiment_label": "Bullish"
    },
    {
      "ticker": "INTC", 
      "relevance_score": "0.7",
      "ticker_sentiment_score": "-0.15",
      "ticker_sentiment_label": "Bearish"
    }
  ],
  "topics": [
    {
      "topic": "earnings",
      "relevance_score": "0.95"
    },
    {
      "topic": "technology",
      "relevance_score": "0.85"
    }
  ]
}
```

## 决策

### 1. 数据结构设计

新增 DataFrame 列：

| 列名 | 类型 | 说明 |
|------|------|------|
| `ticker_sentiments` | str | JSON 格式的个股情绪列表 |
| `topics` | str | 话题标签，格式 "topic1:score,topic2:score" |
| `target_ticker_sentiment` | float | 查询 ticker 的专属情绪分数 (仅 ticker 查询时有值) |
| `target_ticker_label` | str | 查询 ticker 的情绪标签 (仅 ticker 查询时有值) |

### 2. 实现策略

```python
# 解析 ticker_sentiment
ticker_sentiments = article.get("ticker_sentiment", [])
ticker_sentiments_json = json.dumps(ticker_sentiments)

# 提取查询 ticker 的专属情绪
target_sentiment = None
target_label = None
if target_ticker:
    for ts in ticker_sentiments:
        if ts.get("ticker") == target_ticker:
            target_sentiment = ts.get("ticker_sentiment_score")
            target_label = ts.get("ticker_sentiment_label")
            break

# 解析 topics
topics = article.get("topics", [])
topics_str = ",".join([f"{t['topic']}:{t['relevance_score']}" for t in topics])
```

### 3. 函数签名变更

`fetch_news_alphavantage()` 新增可选参数 `target_ticker`:

```python
def fetch_news_alphavantage(
    tickers: Optional[str] = None,
    topics: Optional[str] = None,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    sort: str = "LATEST",
    limit: int = 50,
    target_ticker: Optional[str] = None  # 新增：提取该 ticker 的专属情绪
) -> pd.DataFrame:
```

## 风险 / 权衡

### 风险 1：数据膨胀
- **问题**: `ticker_sentiments` 列可能包含较长的 JSON 字符串
- **缓解**: 使用紧凑 JSON 格式，用户可按需解析

### 风险 2：向后兼容
- **问题**: 新增列可能影响现有代码
- **缓解**: 仅新增列，不修改现有列结构
