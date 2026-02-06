# LLM Skills

一款专为大语言模型 (LLM) 设计的**通用**技能库，旨在通过标准化的 Skill 接口增强模型的各种能力。

## 项目核心

本项目构建了一个模块化的 Skill 体系，使 LLM 能够通过插件化的方式获取实时数据、执行复杂任务或调用外部 API。

项目目前优先开发了**金融数据**类 Skill，提供对全球股市、基金、金属行情及金融新闻的精准检索能力。未来，我们将持续演进并加入更多领域的通用 Skills（如效率工具、数据处理、搜索增强等）。

## 已创建的 Skills 列表

| Skill 名称 | 核心用途 | 数据源 |
| :--- | :--- | :--- |
| **finance-data-china-a-stock** | 抓取中国 A 股历史行情（日/周/月K线）和全市场实时快照。 | akshare |
| **finance-data-hk-stock** | 获取港股历史 K 线及实时行情，支持 5 位代码格式。 | akshare / yfinance |
| **finance-data-us-stock** | 获取美股历史行情、公司基本面信息及市值数据。 | yfinance |
| **finance-data-fund** | 抓取公募基金历史净值及 ETF 历史 K 线数据。 | akshare |
| **finance-data-shanghai-gold** | 抓取上海黄金交易所 (SGE) 黄金现货（如 Au9999）历史行情。 | akshare |
| **finance-data-london-gold** | 抓取 COMEX 黄金期货及国际现货黄金 (XAU/USD) 价格。 | yfinance |
| **finance-data-news** | 抓取全球宏观新闻、特定行业板块新闻及个股情绪分析新闻。 | akshare / Alpha Vantage |

## 快速开始

所有的 Skill 均定义在 `.agent/skills` 目录下。每个 Skill 文件夹内都包含一个 `SKILL.md`，详细说明了具体的功能、调用方法以及参数配置。

### 目录结构

```text
.agent/skills/
├── finance-data-china-a-stock/  # A股数据技能
├── finance-data-fund/          # 基金数据技能
├── finance-data-hk-stock/      # 港股数据技能
├── finance-data-london-gold/   # 国际金价技能
├── finance-data-news/          # 金融新闻技能
├── finance-data-shanghai-gold/ # 沪金数据技能
└── finance-data-us-stock/      # 美股数据技能
```

## 注意事项

- **API 额度**：涉及 Alpha Vantage 的新闻接口每日有调用次数限制（免费账户 25 次）。
- **代码示例**：每个 Skill 的 `SKILL.md` 均提供可以直接运行的 Python 代码示例。
