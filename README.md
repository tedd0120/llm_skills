# LLM Agent Skills Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](#)

面向 **LLM Agent**（Pi、Claude Code、Codex、Cursor、Gemini CLI 等）的本地化技能库。所有技能独立存放于 `.agents/skills/` 目录下，通过结构化的 `SKILL.md`、执行脚本、参考规范与模板，为 Agent 扩展前端与设计系统、数据采集、办公协同、工程编排及系统诊断能力。

---

## 技能矩阵 (Skills Matrix)

每个技能包包含独立的 `SKILL.md` 描述文件，供 Agent 按触发条件自动加载或由用户显式调用。

### 前端与设计系统

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖与运行环境 |
| :--- | :--- | :--- | :--- |
| **`shadcn-ui-workflow`** | 复用现有组件并结合 shadcn/ui、coss ui、Loading UI、Magic UI、Animate UI 与 assistant-ui 选型，支持 Lucide、Tabler、Phosphor、Hugeicons 图标检索与界面适配验证 | 新增或修改 UI 组件、调整界面样式与交互、搜索图标、添加动效与加载状态、构建 AI 对话界面 | 目标前端项目环境 |
| **`website-uiux-extractor`** | 采集目标网址可见 UI/UX，提取带页面、视口和交互状态证据的语义视觉令牌，生成 `DESIGN.md`、DTCG tokens JSON、CSS variables、Tailwind CSS v4 theme 与独立预览页 | 用户提供 URL 并要求提取或复刻网站视觉、整理设计系统、制作视觉令牌 | 可交互浏览器、Python 3.10+ |

### 数据采集与分析

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖与凭证配置 |
| :--- | :--- | :--- | :--- |
| **`xiaohongshu-scraper`** | 协调登录、抓取与后处理组件，完成小红书帖子及评论采集，按推荐选购、方案规划、事实核查或议题探索生成结构化报告 | 用户提到“抓小红书”“爬小红书”“小红书搜索”“分析小红书内容” | Playwright、登录 Cookie |
| **`yushu-sql`** | 通过 OpenCLI 复用 Chrome 登录态，在公司毓数自助查询平台执行、监控、读取或下载 SQL 结果 | 用户提到毓数、自助查询、公司平台跑 SQL、查表取数、导出查询结果或排查查询失败 | OpenCLI、Node.js、Chrome 登录态 |

> `xiaohongshu-scraper` 内部包含 `xiaohongshu-fetch`（数据抓取）、`xiaohongshu-summarize`（报告生成）与 `xiaohongshu-formatter`（格式后处理）三个子组件，由入口技能统一编排调用。

### 办公协同与内网工具

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖与凭证配置 |
| :--- | :--- | :--- | :--- |
| **`teams-attendance`** | 获取 360Teams 考勤明细，计算有效工作日、平均工时与目标达标预测 | 用户查询个人考勤明细、累计工时、工时达标预测 | `TEAMS_EM_CODE`<br>`TEAMS_AUTHORIZATION` |
| **`teams-group-members`** | 获取 360Teams 群组成员并支持多群并集去重，导出标准 JSON 与单文件交互式组织架构树 HTML | 用户需要获取群组成员名单、生成组织架构树 HTML | `TEAMS_AUTHORIZATION`<br>`TEAMS_GROUP_CODES` |
| **`360teams-proxy-repair`** | 检测 Windows 360Teams 是否使用系统代理，诊断待办“非内网办公环境”，在确认客户端强制直连时应用或还原可回滚补丁 | 360Teams 待办提示非内网环境、检测或修复客户端代理转发链路 | Windows、Python 3.10+ |
| **`git-weekly-summary`** | 汇总本周一 00:00 至当前时刻的 Git 提交，按功能模块生成面向非技术读者的精炼中文周报 | 用户显式调用 `$git-weekly-summary` | Git |

### 研发工作流与工程方法

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 调用方式与依赖 |
| :--- | :--- | :--- | :--- |
| **`init`** | 新建项目时初始化 `AGENTS.md`、`CLAUDE.md` 与 `.gitignore`，或对存量项目增量补全开发规范 | 新建项目初始化规范、存量项目补全 `AGENTS.md` 与 `.gitignore` | 自动或手动触发 |
| **`workspace-layout`** | 按“正式资产 / 任务工作区 `.work` / 本机状态 `.local` / 程序自管”四层归位仓库文件，并重审 `.gitignore` | 用户要求“整理工作区”“规范产物目录”“检查哪些目录加入 gitignore” | 自动或手动触发、Python 3.10+ |
| **`subagent-task-runner`** | 按实现计划串行派发独立子代理执行任务，每任务后执行规格与质量审查，全部完成后执行整体审查 | 接收结构化实现计划并分步执行与审查 | 内置 subagent 或 Pi CLI |
| **`agent-council`** | 通过 Pi CLI 与 Claude CLI 将同一任务 prompt 交给多个模型和主 Agent 独立执行并保存报告，供后续比对或裁决 | 需要多模型独立会审、交叉验证或对比不同模型方案 | Pi CLI、Claude CLI |
| **`github-release-updater`** | 为桌面应用制定或审查基于 GitHub Releases 的自动更新方案，覆盖更新器选型、框架与安装方式核查、发布签名流水线与私有 Release 鉴权 | 桌面应用自动更新选型、无自建服务器分发、审查或改造现有更新方案 | 自动或手动触发 |
| **`least-code`** | 提供写新代码时的最小够用准则、清理既有代码过度设计的流程，以及精简评审清单 | 编写、修改、重构、评审代码，或用户提到“简化”“过度设计”“YAGNI” | 自动或手动触发 |
| **`think-like-fable`** | 提供可复现的任务方法论主干，按任务类型路由并加载对应执行框架 | 复杂工程任务需要加载结构化方法论时由用户显式调用 | 仅手动触发 |
| **`brainstorming`** | 陪练式头脑风暴，经过定框、发散、验证假设与收敛，形成带取舍和验证计划的方案文档 | 需要把模糊想法打磨成完整方案文档时由用户显式调用 | 仅手动触发 |

### 系统诊断与实用工具

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖与凭证配置 |
| :--- | :--- | :--- | :--- |
| **`storage-analyzer`** | 扫描 Windows 磁盘占用，生成可勾选清理的本机网页报告，支持缓存回收、系统空间释放与目录迁移方案 | 用户提到“C 盘满了”“磁盘空间不足”“清理磁盘”“清缓存”或刷新清理报告 | Windows、Python 3.10+、`pywin32`、`Send2Trash` |
| **`litellm-model-speedtest`** | 拉取 LiteLLM 网关（或 Anthropic Messages 兼容端点）全部模型并批量流式测速，输出连通性、首字延迟（TTFT）与吞吐率（TPS）排序报告 | 用户要求列出网关全部模型、批量测速、对比不同模型或节点响应速度 | `LLM_API_KEY`、`httpx`、`python-dotenv` |
| **`claude-code-usage`** | 读取本机 `~/.claude/projects` 会话记录，统计 Claude Code 近 7 天与近 30 天的 token 用量汇总表 | 用户询问 Claude Code 用了多少 token、近期用量或花费 | Python 3.10+、Node.js（`npx ccusage`） |
| **`pan123-renamer`** | 扫描 123 云盘视频文件，推断 Emby/Jellyfin 标准命名，经用户确认后批量改名并支持断点续跑与一键回滚 | 用户提到“123网盘重命名”“刮削失败改名”“整理网盘剧集或电影命名” | `PAN123_CLIENT_ID`<br>`PAN123_CLIENT_SECRET` |

---

## 快速开始 (Quick Start)

### 1. 准备基础环境

- 安装 Python 3.10+ 与 Git。
- 使用 `yushu-sql` 或 `claude-code-usage` 时需准备 Node.js 环境。

### 2. 克隆仓库与配置环境变量

```bash
git clone git@github.com:tedd0120/llm_skills.git
cd llm_skills
cp .env.example .env
```

按需在根目录 `.env` 中填入对应技能的凭证配置（`.env` 已列入 `.gitignore`）：

| 环境变量 | 所属技能 | 用途说明 |
| :--- | :--- | :--- |
| `PAN123_CLIENT_ID` / `PAN123_CLIENT_SECRET` | `pan123-renamer` | 123 云盘开放平台开发者凭证 |
| `TEAMS_EM_CODE` | `teams-attendance` | 360Teams 员工编码 |
| `TEAMS_AUTHORIZATION` | `teams-attendance`、`teams-group-members` | 360Teams 接口授权令牌 |
| `TEAMS_GROUP_CODES` | `teams-group-members` | 待拉取成员的群组编码列表（逗号分隔） |
| `LLM_API_KEY` / `LLM_PROXY` | `litellm-model-speedtest` | LiteLLM 网关密钥与可选代理地址 |

### 3. 按需安装技能依赖

各技能独立维护运行依赖，使用前按需安装：

```bash
# 小红书采集组件依赖
pip install -r .agents/skills/xiaohongshu-scraper/scripts/requirements.txt
playwright install chromium

# Windows 磁盘分析清理服务依赖
pip install -r .agents/skills/storage-analyzer/requirements.txt

# LiteLLM 网关测速依赖
pip install httpx python-dotenv

# 123 云盘重命名与 Teams 相关技能依赖
pip install requests python-dotenv
```

---

## 目录与产物约定 (Directory Layout)

仓库采用四层归属管理技能源码、开发过程材料、运行产出与本机状态：

| 路径 | 归属层级 | 说明 | Git 追踪 |
| :--- | :--- | :--- | :--- |
| `.agents/skills/<skill>/` | 正式资产 | 各技能包的 `SKILL.md`、执行脚本 `scripts/`、参考文档 `references/` 与测试 `tests/` | 纳入版本控制 |
| `AGENTS.md` / `CLAUDE.md` | 正式资产 | 仓库级 Agent 行为准则、编码规范与目录约定 | 纳入版本控制 |
| `docs/agents/artifacts.md` | 正式资产 | 开发任务工作区与产物归档规范 | 纳入版本控制 |
| `.env.example` | 正式资产 | 环境变量配置模板 | 纳入版本控制 |
| `data/<skill>/` | 运行产出 | 技能生成的报告、抓取数据与导出文件，按次任务再分 `{年月日}_{时分秒}_{主题}/` 子目录 | 已忽略 |
| `.local/<skill>/` | 本机状态 | 登录态、Cookie、Token 缓存、验证码截图等跨任务复用的本机状态 | 已忽略 |
| `.work/<任务ID>/` | 任务工作区 | 开发任务过程材料（`plan.md`、`prototype/`、`scratch/`、`runner/`、`evidence/`） | 已忽略 |

技能脚本按以下优先级解析产出目录与本机状态目录，不受运行时工作目录影响：

1. 调用方显式传入的输出路径参数；
2. 环境变量 `LLM_SKILLS_DATA_DIR/<skill>`（产出）或 `LLM_SKILLS_STATE_DIR/<skill>`（状态）；
3. 从脚本位置向上查找到的 Git 仓库根目录下的 `data/<skill>` 或 `.local/<skill>`；
4. 用户主目录下的 `~/.llm-skills/data/<skill>` 或 `~/.llm-skills/local/<skill>`。
