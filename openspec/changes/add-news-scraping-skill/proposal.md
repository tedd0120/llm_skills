# 变更：新增时事热点新闻抓取 Skill

## 为什么
为量化分析和投资研究提供新闻舆情数据支持。通过抓取时事热点新闻，可以捕捉市场情绪变化、热点事件冲击，辅助投资决策。支持三种查询维度：全球宏观大盘、特定板块关键词、特定股票/基金代码。

## 变更内容
- 新增 `finance-data-news/` skill 目录
- 创建 `SKILL.md` 使用说明文档
- 创建 `scripts/fetch_news.py` 抓取脚本
- 支持两个数据源：akshare（国内）+ Alpha Vantage（国际）

## 数据源策略

| 数据源 | 适用场景 | API 函数/端点 | 限制 |
|--------|----------|---------------|------|
| akshare | A股个股新闻、国内财经 | `stock_news_em()` | 无明确限制 |
| Alpha Vantage | 全球市场新闻、情绪分析 | `NEWS_SENTIMENT` | 每日25次免费额度 |

## 输入参数设计

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| query_type | str | 查询类型 | `"global"` / `"sector"` / `"ticker"` |
| keyword | str | 板块关键词 | `"technology"`, `"新能源"` |
| ticker | str | 股票/基金代码 | `"000001"`, `"AAPL"` |
| source | str | 数据源 | `"akshare"` / `"alphavantage"` |
| limit | int | 返回条数限制 | 默认 50 |

## 影响
- 受影响规范：无（新增功能）
- 受影响代码：`.agent/skills/` 目录（新增 skill）
- 外部依赖：Alpha Vantage API Key `OPQQYI2WM3MSIN3K`

> [!CAUTION]
> Alpha Vantage 免费账户每日仅有 25 次 API 调用额度，测试时需谨慎使用。
