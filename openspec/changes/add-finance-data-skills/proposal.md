# 变更：添加金融数据抓取 Skills

## 为什么
项目需要建立一套完整的金融数据抓取能力，覆盖多个市场和资产类别，为后续的量化分析、投资研究提供数据基础。通过 Python 的 yfinance 和 akshare 库实现数据抓取，并将其持久化为可复用的 skills。

## 变更内容
- 创建 `.agent/skills/` 目录结构
- 新增 A股数据抓取 skill（使用 akshare）
- 新增基金数据抓取 skill（使用 akshare）
- 新增港股数据抓取 skill（使用 akshare + yfinance）
- 新增美股数据抓取 skill（使用 yfinance）
- 新增沪金数据抓取 skill（使用 akshare）
- 新增伦敦金数据抓取 skill（使用 yfinance）
- 每个 skill 包含 SKILL.md 和示例脚本

## 数据源策略
| 资产类别 | 主要数据源 | 备用数据源 | 说明 |
|---------|-----------|-----------|------|
| A股 | akshare | - | `stock_zh_a_hist()` 提供完整历史数据 |
| 基金 | akshare | - | `fund_etf_hist_em()` / `fund_open_fund_info_em()` |
| 港股 | akshare | yfinance | akshare: `stock_hk_hist()`; yfinance: `.HK` 后缀 |
| 美股 | yfinance | - | 直接使用股票代码如 `AAPL`, `GOOGL` |
| 沪金 | akshare | - | `spot_hist_sge()` 上海黄金交易所数据 |
| 伦敦金 | yfinance | - | 使用 `GC=F` (COMEX金) 或 `XAUUSD=X` 现货金 |

## 影响
- 受影响规范：无（新增功能）
- 受影响代码：`.agent/skills/` 目录（新建）
