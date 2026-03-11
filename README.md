# LLM Skills

本项目汇集了专为 LLM Agent 设计的工具调用技能（Skills），皆在增强 AI 智能体的垂直领域能力，涵盖金融数据获取与办公自动化等场景。

## 📁 技能列表

### 📈 金融数据 (Finance Data)

基于 `akshare` 和 `yfinance` 等数据源，提供全面的市场行情数据支持：

*   **A股 (China A-Stock)** [`finance-data-china-a-stock`]: 获取中国 A 股历史行情与实时数据。
*   **港股 (HK Stock)** [`finance-data-hk-stock`]: 获取香港市场股票数据。
*   **美股 (US Stock)** [`finance-data-us-stock`]: 获取美国市场股票数据。
*   **基金 (Fund)** [`finance-data-fund`]: 获取公募基金产品数据与净值信息。
*   **黄金 (Gold)**:
    *   **上海黄金** [`finance-data-shanghai-gold`]: 获取上海黄金交易所现货数据。
    *   **伦敦金** [`finance-data-london-gold`]: 获取国际现货黄金（伦敦金）行情数据。
*   **财经新闻 (News)** [`finance-data-news`]: 抓取全球财经新闻，支持个股情绪分析、话题标签、涨跌幅排行和内部人交易追踪。

### 🏢 办公自动化 (Office Automation)

*   **Teams 考勤 (Teams Attendance)** [`teams-attendance`]: 自动化处理 Teams 考勤与工时统计生成。
*   **Teams 群组成员 (Teams Group Members)** [`teams-group-members`]: 获取 360Teams 群组成员并生成可离线打开的组织架构树 HTML，支持多群并集去重与结果落盘。

### 🔍 社交媒体 (Social Media)

*   **小红书内容抓取 (Xiaohongshu Scraper)** [`xiaohongshu-scraper-codex`]: 小红书 codex 新架构推荐入口。由单一入口 skill 负责澄清与进度展示，并通过内部 orchestrator 串联抓取、报告生成与最终校验。支持固定关键词模式与发散模式，保留旧版技能作为兼容参考。

    **codex 架构**：
    - [`xiaohongshu-scraper-codex`] - 推荐入口（澄清 + 进度 + orchestrator 调度）
    - [`xiaohongshu-fetch-codex`] - 数据抓取引擎（内部组件）
    - [`xiaohongshu-report-codex`] - 统一报告流水线（内部组件）
    - [`xiaohongshu-core-codex`] - 共享基础层（内部组件）

    **旧版保留**：
    - [`xiaohongshu-scraper`]、[`xiaohongshu-fetch`]、[`xiaohongshu-summarize`]、[`xiaohongshu-formatter`] 继续保留，用于兼容参考与历史行为对照。

## 🚀 使用指南

每个技能文件夹下均包含独立的 `SKILL.md` 文件，详细说明了该技能的：
- **功能描述** (Description)
- **输入参数** (Input Parameters)
- **依赖配置** (Dependencies)
- **使用示例** (Usage Examples)

请查阅具体技能目录下的文档以获取更详细的集成指引。

## 🛠️ 项目结构

```
.claude/skills/
├── finance-data-*/         # 金融相关技能集
├── teams-attendance/       # 考勤自动化技能
├── teams-group-members/    # 群组成员与组织树技能
└── xiaohongshu-*/          # 小红书技能集（scraper, fetch, summarize, formatter, login）
data/                       # 本地数据存储目录（已添加至 .gitignore）
openspec/                   # 开放规范文档
```
