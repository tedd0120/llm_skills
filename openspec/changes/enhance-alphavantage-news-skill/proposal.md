# 变更：增强 Alpha Vantage 新闻 Skill

## 为什么

现有 `finance-data-news` skill 仅使用了 Alpha Vantage API 的 `NEWS_SENTIMENT` 功能，而 API 还提供了多个高价值的 Alpha Intelligence™ 端点未被利用。此增强将拓展 skill 能力，使 LLM 能够获取更全面的市场洞察数据。

## 变更内容

### 新增功能

1. **财报电话会议记录查询** - 使用 `EARNINGS_CALL_TRANSCRIPT` API，获取公司季度财报会议完整记录及LLM情绪分析
2. **美股涨跌幅排行榜** - 使用 `TOP_GAINERS_LOSERS` API，获取当日涨幅/跌幅/成交量Top 20
3. **内部人士交易记录** - 使用 `INSIDER_TRANSACTIONS` API，追踪公司高管、董事等关键人物的买卖行为
4. **增强时间范围筛选** - 完善 `time_from` / `time_to` 参数支持

### 文件变更

| 类型 | 文件 |
|------|------|
| MODIFY | `.agent/skills/finance-data-news/SKILL.md` |
| MODIFY | `.agent/skills/finance-data-news/scripts/fetch_news.py` |

## 数据源详情

| 功能 | API 函数 | 关键参数 | 限制 |
|------|----------|----------|------|
| 财报会议记录 | `EARNINGS_CALL_TRANSCRIPT` | symbol, quarter | 需指定季度 |
| 涨跌幅排行 | `TOP_GAINERS_LOSERS` | 无 | 美股市场 |
| 内部人交易 | `INSIDER_TRANSACTIONS` | symbol | 需指定股票 |

## 影响

- 受影响规范：`alpha-intelligence-data`（新增）
- 受影响代码：`.agent/skills/finance-data-news/`
- 外部依赖：无新增（现有 `ALPHAVANTAGE_API_KEY`）

> [!WARNING]
> Alpha Vantage 免费账户每日仅有 25 次 API 调用额度，新增功能会增加 API 消耗。建议在使用时优先考虑数据价值。
