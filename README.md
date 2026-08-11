# LLM Agent Skills Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](#)

本项目是专为 **LLM Agent**（如 Claude Code, Cursor, Gemini CLI 等）设计的本地化工具调用技能库（Skills Hub）。通过提供结构化的系统提示词（`SKILL.md`）、执行脚本与依赖配置，为 Agent 扩展在办公协同、数据采集、系统分析等特定领域的专业执行能力。

---

## 🛠️ 技能支持矩阵 (Skills Matrix)

所有技能包均独立存放在 `.agents/skills/` 目录下。每个技能包含独立的 `SKILL.md` 配置，以便 Agent 自动发现并加载。

| 技能标识 (ID) | 核心功能 | 适用触发场景 | 依赖/凭证配置 |
| :--- | :--- | :--- | :--- |
| **`xiaohongshu-scraper`** | 小红书帖子/评论自动化爬取及数据分析 | 用户提到“抓取小红书”、“爬取小红书”、“分析小红书帖子”等 | Playwright, 登录 Cookie |
| **`travel-recommend`** | 6 维加权评分的旅游目的地智能推荐与分析报告生成 | 用户提出出游规划、假期去哪玩、旅游攻略推荐等需求 | Tavily MCP (`TAVILY_API_KEY`), 小红书 Cookie |
| **`teams-attendance`** | 360Teams 考勤明细数据分析与工时/预测达标统计 | 用户查询个人考勤明细、累计工时、工时预测等 | `TEAMS_EM_CODE`<br>`TEAMS_AUTHORIZATION` |
| **`teams-group-members`** | 360Teams 群组成员数据抓取与实时检索的组织架构树 HTML 生成 | 用户需要获取群组成员信息、导出架构树 HTML 等 | `TEAMS_AUTHORIZATION`<br>`TEAMS_GROUP_CODES` |
| **`pan123-renamer`** | 123云盘媒体文件智能扫描与 Emby/Jellyfin 标准规范重命名 | 用户提到123网盘文件重命名、规范化媒体库等 | 123云盘开发者凭证 (`PAN123_CLIENT_ID`, `PAN123_CLIENT_SECRET`) |
| **`think-like-fable`** | 软件开发与复杂任务的系统化方法论路由与执行框架 | 接收任何非平凡开发任务（如调试排障、重构、性能优化等）时自动触发 | 无 |
| **`least-code`** | 反过度设计准则：写码前的存在性阶梯、假想敌拦截，以及既有代码的安全精简与评审 | 编写/重构/评审代码，或用户提到“简化”“精简”“过度设计”“YAGNI”“最小实现”等 | 无 |
| **`brainstorming`** | 陪练式头脑风暴：定框→发散→逼问假设→收敛→落地方案文档，深度按赌注与可逆性分档 | **仅手动触发**：Claude `/brainstorming`、Codex `$brainstorming`；禁止自然语言隐式触发 | 无 |

> 💡 **说明**：部分技能包含内部辅助组件（如 `xiaohongshu-fetch`、`xiaohongshu-summarize`、`xiaohongshu-formatter` 等），均由入口技能自动编排调用，无需手动触发。

---

## 🚀 快速开始 (Quick Start)

### 1. 准备环境
- 确保系统已安装 Python 3.8+。
- 确保已安装 Git。

### 2. 克隆项目与配置凭证
```bash
# 克隆仓库
git clone https://github.com/yourusername/llm_skills.git
cd llm_skills

# 创建本地配置文件
cp .env.example .env
```
用编辑器打开 `.env` 并配置您需要启用的技能的相应环境变量（例如，配置 123 云盘的 API 凭证或 Teams 授权令牌）。

### 3. 安装依赖
由于各技能依赖差异较大，推荐使用虚拟环境进行按需安装。例如，要使用 `pan123-renamer` 技能：
```bash
pip install requests
```
如需使用 `xiaohongshu-scraper`，请参照该技能目录下的 [SETUP.md](.agents/skills/xiaohongshu-scraper/SETUP.md) 安装 Playwright 运行环境。

## 📂 项目结构规范

```text
llm_skills/
├── .agents/                    # 智能体技能挂载根目录
│   └── skills/                 # 存放各技能包的源码与 SKILL.md
│       ├── brainstorming/      # 陪练式头脑风暴技能包（仅手动触发）
│       ├── least-code/         # 反过度设计准则技能包
│       ├── pan123-renamer/     # 123云盘重命名技能包
│       ├── teams-attendance/   # Teams考勤分析技能包
│       ├── teams-group-members/# Teams群架构树生成技能包
│       ├── think-like-fable/   # 开发方法论技能包
│       ├── travel-recommend/   # 旅游智能推荐技能包
│       └── xiaohongshu-*/      # 小红书抓取与分析系列包
├── data/                       # 技能执行结果默认输出目录 (如生成的 HTML、Excel、JSON 等)
├── .env.example                # 环境变量配置模板
└── README.md                   # 本说明文档
```
