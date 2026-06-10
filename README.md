# LLM Agent Skills Hub 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Platform: macOS & Windows](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](#)

本项目是一个专为 **LLM Agent**（如 Claude Code、Cursor、Gemini CLI 等）量身定制的**工具调用技能库（Skills Hub）**。

通过向 Agent 提供结构化的提示词、执行脚本与依赖配置，本项目赋予了 Agent 在 **办公自动化、社交数据抓取、深度行业研究、系统存储清理** 等场景下的垂直领域专业执行能力，让 AI 智能体真正成为可靠的本地生产力助手。

---

## 📂 技能库概览 (Skills Matrix)

项目所有技能均遵循 Agent 统一调用标准，以独立的目录形式管理。每个目录下均有独立的 `SKILL.md`，包含功能说明、参数列表、依赖配置和使用示例。

| 技能名称 / 标识符 | 类别 | 功能描述 | 外部依赖 / 配置 | 开源来源归属 |
| :--- | :--- | :--- | :--- | :--- |
| **实时 AI 资讯查询**<br>`[aihot]` | 📰 资讯/大模型 | 实时拉取并整理 `aihot.virxact.com` 的 AI 每日简报、精选热点与模型/产品发布动态。 | 无需 Token，需指定 `User-Agent` 标识 | 🔗 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) |
| **横纵分析法深度研究**<br>`[hv-analysis]` | 📊 深度行业研究 | 双轴（纵轴历时演进、横轴共时对比）深度研究框架，系统性调研产品/公司/概念，自动生成 PDF 报告。 | `weasyprint`, `markdown` 库 | 🔗 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) |
| **只读存储分析助手**<br>`[storage-analyzer]` | 🛠️ 系统工具 | 深度扫描整机磁盘占用，提供绿/黄/红三级清理决策清单，并可启动本地 Web 服务一键清理。 | Python 3 标准库（零第三方依赖） | 🔗 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) |
| **小红书内容分析套件**<br>`[xiaohongshu-scraper]` | 📲 社交媒体数据 | 一站式小红书内容抓取与分析，支持固定关键词和 AI 发散搜索，最终生成结构化分析报告。 | Playwright 浏览器自动化 / 登录 Cookie | 本项目原创开发 |
| **汉庭人流量指数**<br>`[huazhu-crowd-index]` | ✈️ 旅游/人流分析 | 监控携程网「汉庭」酒店特定日期 vs 节后平日的价格涨幅，横向评估对比全国热门城市人流热度。 | 携程网 Cookie 授权 | 本项目原创开发 |
| **Teams 考勤工时统计**<br>`[teams-attendance]` | 💼 办公自动化 | 抓取 360Teams 考勤明细，自动统计有效工作日与平均工时，预测日均目标并导出 CSV。 | `TEAMS_AUTHORIZATION`<br>`TEAMS_EM_CODE` | 本项目原创开发 |
| **Teams 群组成员架构**<br>`[teams-group-members]` | 💼 办公自动化 | 批量获取 Teams 群组成员并去重，自动补齐虚拟上级，生成支持拖拽与检索的离线 HTML 组织树。 | `TEAMS_AUTHORIZATION`<br>`TEAMS_GROUP_CODES` | 本项目原创开发 |

> [!NOTE]
> 小红书数据分析套件包含底层子组件：`xiaohongshu-fetch` (数据抓取引擎)、`xiaohongshu-summarize` (分析报告生成)、`xiaohongshu-formatter` (后处理格式化)，这些子组件由主入口 `xiaohongshu-scraper` 统一编排调度。

---

## 🌟 核心技能亮点介绍

### 📰 AI 行业资讯与深度研究

#### 1. 实时 AI 资讯查询 ([aihot](file:///.agents/skills/aihot))
* **核心功能**：让 Agent 用最自然的中文调取最新的 AI HOT 资讯。支持获取今日日报、精选条目或针对特定主题（如 "Sora", "RAG"）进行全文检索。
* **技术特性**：实时连通 Web API，绕过传统 LLM 模型的训练时间限制；内置完备的 API 请求限流（600 req/min/IP）和 `User-Agent` 伪装防护。
* **来源归属**：该技能方案与设计源自开源项目 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills)。

#### 2. 横纵分析法深度研究 ([hv-analysis](file:///.agents/skills/hv-analysis))
* **核心功能**：对特定产品、公司、技术概念或人物进行双轴深度研究。纵轴追踪从诞生到当下的生命历程（以故事呈现），横轴在当下时间截面上与同类竞品进行系统对比，最终交叉产出独到洞察。
* **技术特性**：支持多 Agent 并行执行检索与汇总；集成了基于 `WeasyPrint` 的 PDF 渲染脚本，可从生成的 Markdown 报告一键转为高颜值排版 PDF。
* **来源归属**：该方法论与技能模板源自开源项目 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills)。

---

### 🛠️ 系统工具与数据分析

#### 3. 只读存储分析助手 ([storage-analyzer](file:///.agents/skills/storage-analyzer))
* **核心功能**：一键分析磁盘空间占用，智能识别应用缓存（🟢可清）、用户数据（🟡需人工判定）和系统应用（🔴谨慎清理），并给出卸载/清理的步骤建议。
* **技术特性**：扫描过程严格只读；支持以本地 HTTP 服务（`server.py`）启动交互式 HTML 报告页面，提供安全的「移至废纸篓」与「直接删除」操作，具备全面的跨平台（macOS/Windows）防护机制。
* **来源归属**：该系统分析与清理报告工具源自开源项目 [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills)。

#### 4. 小红书数据分析套件 ([xiaohongshu-scraper](file:///.agents/skills/xiaohongshu-scraper))
* **核心功能**：一站式小红书内容抓取与分析入口。支持固定关键词模式与 AI 主题发散多轮搜索，通过浏览器自动化抓取帖子和评论数据，最终生成结构化 Markdown 报告。
* **技术特性**：支持安全/正常/极速三档延迟模式规避风控；全自动 Cookie 管理及登录状态检测。

#### 5. 汉庭人流量指数分析 ([huazhu-crowd-index](file:///.agents/skills/huazhu-crowd-index))
* **核心功能**：同一家酒店在节假日价格暴涨，直接反应了该城市该日的人流量热度。本技能每城锚定一家基础型汉庭酒店做横向对比，评估各大城市节假日人流量排名。
* **技术特性**：支持 16 个内置热门城市或自定义城市清单，自动计算节日价 vs 节后首个周二平日价的价格涨幅倍数，产出城市热度排名报告。

---

### 💼 办公自动化 (Office Automation)

#### 6. Teams 考勤工时统计 ([teams-attendance](file:///.agents/skills/teams-attendance))
* **核心功能**：从 360Teams 平台获取员工考勤明细，计算已工作天数、累计工时、当前平均工时，并基于 10.5 / 10.7 / 11 小时等不同考勤目标预测后续日均所需工时，支持考勤明细导出为 CSV。

#### 7. Teams 群组成员架构 ([teams-group-members](file:///.agents/skills/teams-group-members))
* **核心功能**：批量获取 360Teams 群组成员数据，按工号并集去重，并根据汇报线自动补齐虚拟上级节点。生成一个可离线打开的 HTML 树状图，支持缩放拖拽、姓名/工号/部门双维度实时检索与导航定位。

---

## ⚙️ 快速上手与配置指南

### 📁 项目目录结构

```text
llm_skills/
├── .agents/                    # 兼容部分第三方智能体平台的技能目录
│   └── skills/                 # 存放各技能包的源码与 SKILL.md
├── .claude/                    # Claude Code 默认加载的技能目录
│   └── skills/                 # 核心技能源文件目录（内含各技能的 SKILL.md）
│       ├── aihot/
│       ├── huazhu-crowd-index/
│       ├── hv-analysis/
│       ├── storage-analyzer/
│       ├── teams-attendance/
│       ├── teams-group-members/
│       └── xiaohongshu-*/
├── data/                       # 技能执行结果默认输出与落盘目录
├── .env.example                # 环境变量配置模板
└── README.md                   # 项目中文说明文档
```

### 1. 安装系统依赖
若要使用 `hv-analysis` (PDF 生成) 技能，需要在宿主机安装 PDF 渲染工具 `WeasyPrint`：
* **Windows**：
  ```bash
  pip install weasyprint markdown --break-system-packages
  ```
* **macOS**：
  ```bash
  brew install weasyprint
  pip3 install weasyprint markdown
  ```

### 2. 环境变量配置
在项目根目录下复制并创建 `.env` 文件：
```bash
cp .env.example .env
```
根据所使用的技能填入相应的 API Key 与账号授权 Token（如 Teams 相关的 `TEAMS_AUTHORIZATION` 等）。详细的变量说明请直接参考 [.env.example](file:///p:/git_repos/llm_skills/.env.example)。

```env
# Teams 相关技能配置
TEAMS_AUTHORIZATION=你的授权令牌
TEAMS_EM_CODE=你的员工编码          # teams-attendance 专用
TEAMS_GROUP_CODES=群组A,群组B       # teams-group-members 专用
```

### 3. 在 Agent 中注册使用
以 **Claude Code** 为例：
1. Claude Code 启动时会自动加载工作区根目录下 `.claude/skills/` 下的技能。
2. 当你在对话中提出相关需求（如 *"帮我看看我的 C 盘空间"* 或 *"查一下最近 AI 圈的模型发布"*）时，Claude Code 会根据技能的 `SKILL.md` 描述自动拉起对应的 Python 或 Shell 脚本执行。

---

## 🤝 参与贡献 (Contributing)
非常欢迎为本项目提交新的 Agent 实用技能！
1. Fork 本仓库。
2. 在 `.claude/skills/` 下新建你的技能文件夹（包含 `SKILL.md` 与脚本代码）。
3. 提交 Pull Request 并详细描述测试案例。

## 📄 开源协议 (License)
本项目基于 **MIT** 协议开源，部分技能组件来源已在 [技能库概览](#-技能库概览-skills-matrix) 中明确标出。在此特别感谢相关开源项目作者的杰出工作。
