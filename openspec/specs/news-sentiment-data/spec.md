# news-sentiment-data 规范

## 目的
待定 - 由归档变更 enhance-news-sentiment-parsing 创建。归档后请更新目的。
## 需求
### 需求：个股专属情绪解析

系统**必须**解析并返回每篇新闻中各个相关股票的专属情绪分数和标签。当查询特定股票时，系统**必须**优先提取该股票的专属情绪。

#### 场景：查询 AAPL 新闻并获取专属情绪

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_news(query_type="ticker", ticker="AAPL")`  
**那么** 返回的 DataFrame 包含 `target_ticker_sentiment` 列，值为 AAPL 的专属情绪分数  
**并且** 包含 `target_ticker_label` 列，值为 AAPL 的情绪标签（如 Bullish/Bearish）

#### 场景：获取所有相关股票的情绪

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_news(query_type="global")`  
**那么** 返回的 DataFrame 包含 `ticker_sentiments` 列，值为 JSON 格式的个股情绪列表

---

### 需求：话题标签解析

系统**必须**解析并返回每篇新闻的话题标签及其相关度分数。

#### 场景：获取新闻话题标签

**假设** 用户设置了有效的 `ALPHAVANTAGE_API_KEY` 环境变量  
**当** 用户调用 `fetch_news(query_type="global")`  
**那么** 返回的 DataFrame 包含 `topics` 列  
**并且** 列值格式为 "topic1:score,topic2:score"

