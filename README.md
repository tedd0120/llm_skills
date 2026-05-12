# LLM Skills

本项目汇集了专为 LLM Agent 设计的工具调用技能（Skills），旨在增强 AI 智能体的垂直领域能力，涵盖办公自动化与社交媒体内容分析等场景。

## 技能列表

### 办公自动化

**Teams 考勤** [`teams-attendance`]

从 360Teams 平台获取员工考勤数据，计算有效工作日和平均工时，并按标准模板回复。

- 考勤明细获取（支持指定月份）
- 已工作天数、累计工时、当前平均工时统计
- 基于 10.5 / 10.7 / 11 小时目标的剩余日均工时预测
- 考勤明细 CSV 导出

---

**Teams 群组成员** [`teams-group-members`]

获取 360Teams 群组成员并生成可离线打开的组织架构树 HTML，支持多群并集去重与结果落盘。

- 单群或多群批量抓取，按工号去重
- 虚拟上级节点自动补齐
- 生成离线单文件 HTML：支持缩放拖拽、姓名/工号/部门搜索、命中导航、详情面板、紧凑/默认双密度布局

---

### 社交媒体

**小红书内容抓取** [`xiaohongshu-scraper`]

一站式小红书内容抓取与分析入口，协调登录、抓取、报告生成的完整流程。

支持两种搜索模式：
- **固定关键词模式**：用户确认关键词列表，系统一次性执行搜索
- **发散模式**：AI 从主题出发自动多轮搜索，每轮根据上轮发现动态决定下一关键词

速度模式：安全模式（增大延迟规避风控）/ 正常模式 / 极速模式

**架构**（四层组件）：

| 组件 | 职责 |
|------|------|
| [`xiaohongshu-scraper`] | 编排层入口：澄清阶段、任务调度、进度管理 |
| [`xiaohongshu-fetch`] | 数据抓取引擎：浏览器自动化，输出 raw.json（内部） |
| [`xiaohongshu-summarize`] | 报告生成：分析数据，输出结构化 Markdown 报告（内部） |
| [`xiaohongshu-formatter`] | 格式化：增强 emoji，替换超链接占位符（内部） |

## 快速上手

每个技能目录下均有独立的 `SKILL.md`，包含功能说明、参数列表、依赖配置和使用示例。

```
.claude/skills/
├── teams-attendance/          # 考勤数据与工时统计
├── teams-group-members/       # 群组成员与组织架构树 HTML
└── xiaohongshu-*/             # 小红书技能集（scraper, fetch, summarize, formatter）
```

### 前置配置

在项目根目录创建 `.env` 文件并填写以下环境变量：

```env
# Teams 相关技能
TEAMS_AUTHORIZATION=你的授权令牌
TEAMS_EM_CODE=你的员工编码          # teams-attendance 专用
TEAMS_GROUP_CODES=群组A,群组B       # teams-group-members 专用

# 小红书无需额外环境变量，Cookie 由登录流程自动管理
```
