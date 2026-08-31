# LLM Agent Skills Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](#)

本项目是专为 **LLM Agent**（如 Claude Code, Cursor, Gemini CLI 等）设计的本地化工具调用技能库（Skills Hub）。通过提供结构化的系统提示词（`SKILL.md`）、执行脚本与依赖配置，为 Agent 扩展在办公协同、数据采集、系统分析等特定领域的专业执行能力。

---

## 技能支持矩阵 (Skills Matrix)

所有技能包均独立存放在 `.agents/skills/` 目录下。每个技能包含独立的 `SKILL.md` 配置，以便 Agent 自动发现并加载。

### 数据采集与分析

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖/凭证配置 |
| :--- | :--- | :--- | :--- |
| **`xiaohongshu-scraper`** | 小红书帖子/评论自动化爬取及数据分析 | 用户提到"抓取小红书"、"爬取小红书"、"分析小红书帖子"等 | Playwright, 登录 Cookie |
| **`yushu-sql`** | 通过 OpenCLI 复用 Chrome 登录态，在公司毓数平台执行、监控、读取或下载 SQL 结果 | 用户提到毓数、自助查询、跑 SQL、查表取数、导出查询结果等 | OpenCLI, Chrome 登录态 |
| **`website-uiux-extractor`** | 从网址系统采集可见 UI/UX，生成语义视觉令牌、DESIGN.md、DTCG tokens JSON、CSS variables 等设计系统产物 | 用户给出 URL 并要求提取或复刻网站视觉、整理设计系统 | 可交互浏览器 |

### 办公协同

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖/凭证配置 |
| :--- | :--- | :--- | :--- |
| **`teams-attendance`** | 360Teams 考勤明细数据分析与工时/预测达标统计 | 用户查询个人考勤明细、累计工时、工时预测等 | `TEAMS_EM_CODE`<br>`TEAMS_AUTHORIZATION` |
| **`teams-group-members`** | 360Teams 群组成员数据抓取与组织架构树 HTML 生成 | 用户需要获取群组成员信息、导出架构树 HTML 等 | `TEAMS_AUTHORIZATION`<br>`TEAMS_GROUP_CODES` |
| **`git-weekly-summary`** | 将本周 Git 提交整理成面向非技术读者的精炼中文周报 | 用户显式调用 `$git-weekly-summary` | 无 |

### 工具与基础设施

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖/凭证配置 |
| :--- | :--- | :--- | :--- |
| **`pan123-renamer`** | 123云盘媒体文件智能扫描与 Emby/Jellyfin 标准规范重命名 | 用户提到123网盘文件重命名、规范化媒体库等 | `PAN123_CLIENT_ID`<br>`PAN123_CLIENT_SECRET` |
| **`litellm-model-speedtest`** | LiteLLM 网关全量模型列举与批量测速，输出连通性、首字延迟(TTFT)、token/秒排序报告 | 用户要求列出网关所有模型、测速、对比模型速度等 | `LLM_API_KEY`（仓库根 `.env`） |
| **`agent-council`** | 将同一条 prompt 交给多个模型和主 Agent 独立完成，保存各自报告供后续比较 | 用户需要多模型会审、交叉验证、对比不同模型输出 | Pi CLI, Claude CLI |
| **`subagent-task-runner`** | 按实现计划串行派发 subagent 执行任务，每任务后审查，全部完成后整体审查 | 接收结构化实现计划，需要高质量分步执行 | 无 |

### 方法论与质量

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖/凭证配置 |
| :--- | :--- | :--- | :--- |
| **`think-like-fable`** | 软件开发与复杂任务的系统化方法论路由与执行框架 | 接收任何非平凡开发任务（如调试、重构、性能优化等）时自动触发 | 无 |
| **`least-code`** | 反过度设计准则：写码前的存在性阶梯、假想敌拦截，以及既有代码的安全精简与评审 | 编写/重构/评审代码，或用户提到"简化""精简""YAGNI"等 | 无 |
| **`no-negative-echo`** | 清除交付面中仅存在于工作会话的负向回声，让产物只描述已接受的终态 | 用户纠正、方案淘汰或多轮迭代后生成最终交付物 | 无 |
| **`brainstorming`** | 陪练式头脑风暴：定框、发散、逼问假设、收敛、落地方案文档 | **仅手动触发**：Claude `/brainstorming`、Codex `$brainstorming` | 无 |

> 部分技能包含内部辅助组件（如 `xiaohongshu-fetch`、`xiaohongshu-summarize`、`xiaohongshu-formatter` 等），均由入口技能自动编排调用，无需手动触发。

---

## 快速开始 (Quick Start)

### 1. 准备环境
- 确保系统已安装 Python 3.8+。
- 确保已安装 Git。

### 2. 克隆项目与配置凭证
```bash
# 克隆仓库
git clone https://github.com/yourusername/llm_skills.git
cd llm_skills
```
在仓库根目录创建 `.env` 文件，配置您需要启用的技能的相应环境变量（例如 123 云盘 API 凭证、Teams 授权令牌、LiteLLM API Key 等）。

### 3. 安装依赖
各技能依赖差异较大，推荐按需安装。例如：
- 使用 `pan123-renamer`：`pip install requests`
- 使用 `xiaohongshu-scraper`：参照 [SETUP.md](.agents/skills/xiaohongshu-scraper/SETUP.md) 安装 Playwright 运行环境
- 使用 `litellm-model-speedtest`：`pip install httpx python-dotenv`
- 使用 `yushu-sql`：需要安装 OpenCLI 并配置 Chrome 浏览器桥接

## 项目结构

```text
llm_skills/
├── .agents/                         # 智能体技能挂载根目录
│   └── skills/                      # 存放各技能包的源码与 SKILL.md
│       ├── agent-council/           # 多模型会审技能包
│       ├── brainstorming/           # 陪练式头脑风暴技能包（仅手动触发）
│       ├── git-weekly-summary/      # Git 周报生成技能包
│       ├── least-code/              # 反过度设计准则技能包
│       ├── litellm-model-speedtest/ # LiteLLM 网关模型测速技能包
│       ├── no-negative-echo/        # 交付面负向回声清除技能包
│       ├── pan123-renamer/          # 123云盘重命名技能包
│       ├── subagent-task-runner/    # Subagent 分步执行框架
│       ├── teams-attendance/        # Teams 考勤分析技能包
│       ├── teams-group-members/     # Teams 群架构树生成技能包
│       ├── think-like-fable/        # 开发方法论技能包
│       ├── website-uiux-extractor/  # 网站 UI/UX 视觉令牌提取技能包
│       ├── xiaohongshu-scraper/     # 小红书抓取入口技能包
│       ├── xiaohongshu-fetch/       # 小红书数据抓取组件（内部）
│       ├── xiaohongshu-formatter/   # 小红书报告格式化组件（内部）
│       ├── xiaohongshu-summarize/   # 小红书报告生成组件（内部）
│       └── yushu-sql/               # 毓数 SQL 查询技能包
├── data/                            # 技能执行结果默认输出目录（已 gitignore）
└── README.md                        # 本说明文档
```
