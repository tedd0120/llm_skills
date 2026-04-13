# LLM Skills

本项目汇集了专为 LLM Agent 设计的工具调用技能（Skills），旨在增强 AI 智能体的垂直领域能力，涵盖办公自动化与社交媒体内容分析等场景。

## 📁 技能列表

### 🏢 办公自动化 (Office Automation)

*   **Teams 考勤 (Teams Attendance)** [`teams-attendance`]: 自动化处理 Teams 考勤与工时统计生成。
*   **Teams 群组成员 (Teams Group Members)** [`teams-group-members`]: 获取 360Teams 群组成员并生成可离线打开的组织架构树 HTML，支持多群并集去重与结果落盘。

### 🔍 社交媒体 (Social Media)

*   **小红书内容抓取 (Xiaohongshu Scraper)** [`xiaohongshu-scraper`]: 一站式小红书内容抓取与分析入口。

    **架构说明**：
    - [`xiaohongshu-scraper`] - 编排层入口，负责澄清阶段、任务调度与进度管理
    - [`xiaohongshu-fetch`] - 数据抓取引擎，执行浏览器自动化抓取（内部组件）
    - [`xiaohongshu-summarize`] - 报告生成组件，分析数据并输出结构化报告（内部组件）
    - [`xiaohongshu-formatter`] - 格式化组件，增强报告可读性与 emoji（内部组件）

    **核心特性**：
    - 支持固定关键词模式与 AI 发散模式
    - 自动登录检测与扫码登录
    - 多轮发散搜索，动态决定下一关键词
    - 任务清单验证，确保流程完整性

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
├── teams-attendance/       # 考勤自动化技能
├── teams-group-members/    # 群组成员与组织树技能
└── xiaohongshu-*/          # 小红书技能集（scraper, fetch, summarize, formatter）
```
