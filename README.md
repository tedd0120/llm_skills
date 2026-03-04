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

*   **小红书内容抓取 (Xiaohongshu Scraper)** [`xiaohongshu-scraper`]: 通过 Playwright 自动化浏览器抓取小红书帖子正文与评论区内容。支持 QR 码扫码登录、Cookie 持久化、多关键词搜索与去重、反风控策略。Agent 层自动生成衍生搜索词并对原始内容进行 AI 总结，按帖子输出独立 Markdown 文件。`_index.md` 默认要求输出“深度汇总报告”（含单篇结构化摘要、跨帖共识/分歧、风险与信息缺口），禁止“一句话判语”或纯榜单式收尾。跨平台支持 Windows (msedge) 和 Linux (Xvfb 虚拟显示器)。

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
└── xiaohongshu-scraper/    # 小红书内容抓取与AI总结技能
data/                       # 本地数据存储目录（已添加至 .gitignore）
openspec/                   # 开放规范文档
```
