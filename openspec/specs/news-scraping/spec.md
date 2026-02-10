# news-scraping 规范

## 目的
定义财经新闻抓取与过滤能力的统一规范，覆盖宏观、板块与个股场景，并约束输出结构与额度保护，支持后续情绪分析和交易决策输入。
## 需求
### 需求：抓取全球宏观新闻
系统**必须**通过 Alpha Vantage API 获取全球宏观经济相关的时事新闻和市场情绪数据。

#### 场景：获取全球宏观大盘新闻
```gherkin
Given 用户指定查询类型为 "global"
And 数据源为 "alphavantage"
When 调用 fetch_news() 函数
Then 系统必须返回包含宏观经济新闻的 DataFrame
And 每条新闻必须包含标题、摘要、发布时间、来源链接
And 每条新闻必须包含情绪分数 sentiment_score
```

---

### 需求：按板块关键词抓取新闻
系统**必须**支持按行业板块关键词过滤新闻，适用于板块轮动分析。

#### 场景：获取科技板块新闻
```gherkin
Given 用户指定查询类型为 "sector"
And 关键词为 "technology"
And 数据源为 "alphavantage"
When 调用 fetch_news(query_type="sector", keyword="technology") 函数
Then 系统必须返回科技行业相关的新闻 DataFrame
And 新闻内容必须与科技行业相关
```

#### 场景：支持的板块关键词
```gherkin
Given 以下板块关键词必须有效:
  | 关键词 | 说明 |
  | technology | 科技 |
  | blockchain | 区块链 |
  | earnings | 财报 |
  | ipo | IPO |
  | mergers_and_acquisitions | 并购 |
  | financial_markets | 金融市场 |
  | economy_fiscal | 财政政策 |
  | economy_monetary | 货币政策 |
  | economy_macro | 宏观经济 |
  | energy_transportation | 能源交通 |
  | life_sciences | 生命科学 |
  | manufacturing | 制造业 |
  | real_estate | 房地产 |
  | retail_wholesale | 零售批发 |
  | finance | 金融 |
When 用户传入有效关键词
Then 系统必须返回对应板块的新闻数据
```

---

### 需求：按股票代码抓取新闻
系统**必须**支持通过股票/基金代码获取相关新闻，适用于个股研究。

#### 场景：获取 A股个股新闻（使用 akshare）
```gherkin
Given 用户指定股票代码为 "000001"
And 代码格式为 A股（纯数字6位）
When 调用 fetch_news(query_type="ticker", ticker="000001") 函数
Then 系统必须自动使用 akshare 数据源
And 系统必须调用 stock_news_em() 获取东方财富新闻
And 返回的 DataFrame 必须包含新闻标题、内容、发布时间、链接
```

#### 场景：获取美股/港股个股新闻（使用 Alpha Vantage）
```gherkin
Given 用户指定股票代码为 "AAPL"
And 代码格式为非 A股
When 调用 fetch_news(query_type="ticker", ticker="AAPL", source="alphavantage") 函数
Then 系统必须使用 Alpha Vantage NEWS_SENTIMENT API
And 系统必须返回包含情绪分析的新闻 DataFrame
```

---

### 需求：限制返回条数
系统**必须**支持通过 limit 参数控制返回的新闻数量。

#### 场景：限制返回 10 条新闻
```gherkin
Given 用户指定 limit=10
When 调用 fetch_news(limit=10) 函数
Then 系统必须返回最多 10 条新闻记录
```

---

### 需求：API 额度保护
Alpha Vantage 免费账户每日仅 25 次调用，系统**必须**保护 API 额度。

#### 场景：显示 API 调用提示
```gherkin
Given 用户使用 alphavantage 数据源
When 调用 fetch_news() 函数
Then 系统必须打印 API 调用提示信息
And 系统必须提醒用户每日额度限制
```
