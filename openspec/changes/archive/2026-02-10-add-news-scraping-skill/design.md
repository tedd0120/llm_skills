# 设计文档：时事热点新闻抓取 Skill 架构

## 上下文
需要创建一个新闻抓取 skill，支持从多个维度获取金融市场相关的时事新闻：
1. **全球宏观大盘** - 获取宏观经济、货币政策等全球性新闻
2. **特定板块关键词** - 获取科技、新能源、医药等行业板块新闻
3. **特定股票/基金代码** - 获取与具体标的相关的新闻

### 约束
- 使用 akshare 作为国内数据源
- 使用 Alpha Vantage 作为国际数据源（每日 25 次免费额度）
- 遵循现有 `.agent/skills/` 目录结构

## 目标 / 非目标

### 目标
- 统一的新闻抓取接口，支持多数据源
- 支持三种查询维度（全球宏观、板块、个股）
- 返回结构化的 DataFrame 数据
- 包含新闻标题、内容摘要、发布时间、来源链接

### 非目标
- 不实现新闻情感分析（Alpha Vantage 已提供内置情绪分数）
- 不实现实时新闻推送
- 不构建新闻存储数据库

## 决策

### 1. Skill 目录结构
```
.agent/skills/finance-data-news/
├── SKILL.md              # 使用说明
└── scripts/
    └── fetch_news.py     # 抓取脚本
```

### 2. 数据源分工

| 查询类型 | akshare | Alpha Vantage |
|----------|---------|---------------|
| A股个股新闻 | ✅ `stock_news_em()` | ❌ 不支持 |
| 全球宏观 | ❌ 有限支持 | ✅ `topics=economy_macro` |
| 板块关键词 | ❌ 有限支持 | ✅ `topics=xxx` |
| 美股/港股个股 | ❌ | ✅ `tickers=xxx` |

### 3. Alpha Vantage API 详解

**端点**: `https://www.alphavantage.co/query`

**参数**:
- `function=NEWS_SENTIMENT` (必需)
- `tickers`: 股票/加密货币代码，如 `AAPL`, `CRYPTO:BTC`
- `topics`: 主题过滤，支持:
  - `economy_macro` - 宏观经济
  - `economy_fiscal` - 财政政策
  - `economy_monetary` - 货币政策
  - `financial_markets` - 金融市场
  - `technology` - 科技
  - `blockchain` - 区块链
  - `earnings` - 财报
  - `ipo` - IPO
  - `mergers_and_acquisitions` - 并购
  - `energy_transportation` - 能源交通
  - `life_sciences` - 生命科学
  - `manufacturing` - 制造业
  - `real_estate` - 房地产
  - `retail_wholesale` - 零售批发
  - `finance` - 金融
- `time_from` / `time_to`: 时间范围 `YYYYMMDDTHHMM`
- `sort`: 排序方式 `LATEST` / `EARLIEST` / `RELEVANCE`
- `limit`: 返回条数，默认 50，最大 1000
- `apikey`: API 密钥

### 4. 输出数据格式

统一输出 DataFrame，列包含：
- `title` - 新闻标题
- `summary` - 内容摘要
- `source` - 来源
- `url` - 原文链接
- `published_time` - 发布时间
- `sentiment_score` - 情绪分数（仅 Alpha Vantage）
- `tickers` - 关联股票代码

### 5. API Key 管理

Alpha Vantage API Key: `Env Var: ALPHAVANTAGE_API_KEY`
- ❌ **严禁硬编码**：不要将 API Key 写入代码
- ✅ **推荐方式**：仅通过环境变量 `ALPHAVANTAGE_API_KEY` 获取

## 风险 / 权衡

### 风险 1：Alpha Vantage API 额度限制
- **问题**: 每日仅 25 次免费调用
- **缓解**: 
  - 脚本增加调用计数提示
  - 测试用例仅运行一次
  - 优先使用 akshare 获取国内数据

### 风险 2：新闻数据时效性
- **问题**: akshare 新闻可能有延迟
- **缓解**: 文档中说明数据时效特性

### 风险 3：代码识别差异
- **问题**: A股代码（000001） vs 美股代码（AAPL）格式不同
- **缓解**: 根据代码格式自动判断市场，路由到对应数据源

## 待决问题
- [x] 是否需要缓存机制？ → 暂不需要，简化实现
- [x] 是否支持批量多股票查询？ → 是，Alpha Vantage 支持逗号分隔
