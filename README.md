# LLM Agent Skills Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Platform: macOS & Windows](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-blue.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](#)

本项目是专为 **LLM Agent**（如 Claude Code、Cursor、Gemini CLI 等）设计的本地化工具调用技能库（Skills Hub）。通过提供结构化的系统提示词（`SKILL.md`）、执行脚本与依赖配置，为 Agent 扩展在办公自动化、数据采集、系统分析等特定领域的专业执行能力。

## 快速开始 (Quick Start)

### 1. 环境准备
- 操作系统：macOS / Windows
- Python 3.8+

### 2. 获取项目与配置
```bash
git clone https://github.com/yourusername/llm_skills.git
cd llm_skills

# 复制环境变量配置
cp .env.example .env
```
根据需要编辑 `.env` 文件，填入所需技能的鉴权 Token（如 `TEAMS_AUTHORIZATION`）。详见 `.env.example`。

### 3. 安装依赖
基础技能开箱即用，部分复杂技能如果需要特定运行环境，请参考各技能目录下的 `SKILL.md` 指南。

### 4. 在 Agent 中触发调用
以 **Claude Code** 为例：
工作区根目录的 `.claude/skills/`（或 `.agents/skills/`）会被自动加载。在对话中输入特定意图即可触发：
> "帮我分析下某篇小红书笔记" -> 触发 `xiaohongshu-scraper`
> "统计一下我上个月的考勤记录" -> 触发 `teams-attendance`

---

## 技能支持矩阵 (Skills Matrix)

所有技能均以独立目录形式管理，核心指令与说明封装于各目录下的 `SKILL.md` 中。

| 技能标识符 | 领域 | 功能说明 | 依赖要求 |
| :--- | :--- | :--- | :--- |
| **`xiaohongshu-scraper`**| 数据采集 | 提供帖子与评论自动化抓取及分析，支持关键词搜索与 AI 发散搜索。内置多级延迟与 Cookie 状态管理。 | Playwright / 登录 Cookie |
| **`huazhu-crowd-index`**| 数据分析 | 通过监控携程网上各大城市基础型汉庭酒店的"节假日涨幅倍数"，横向对比并评估目标城市的假期人流量热度。 | 携程网 Cookie |
| **`teams-attendance`** | 办公协同 | 抓取 360Teams 考勤明细，计算已工作时长、预测日均达标工时，支持导出 CSV。 | `TEAMS_AUTHORIZATION`<br>`TEAMS_EM_CODE` |
| **`teams-group-members`**| 办公协同 | 批量获取 360Teams 群组成员，基于汇报线自动补全组织架构树，并生成支持实时检索的离线 HTML 视图。 | `TEAMS_AUTHORIZATION`<br>`TEAMS_GROUP_CODES` |

---

## 项目架构与规范

```text
llm_skills/
├── .agents/                    # 第三方智能体通用技能挂载目录
│   └── skills/                 # 存放各技能包的源码与 SKILL.md
├── .claude/                    # Claude Code 默认技能加载目录
│   └── skills/                 
│       ├── teams-attendance/
│       ├── xiaohongshu-scraper/
│       └── ...
├── data/                       # 技能执行结果默认输出目录
└── .env.example                # 环境变量模板
```

每个技能遵循相同的接入规范，目录内必须包含 `SKILL.md`，用于向 Agent 声明：
- **触发意图**：何时应该调用该技能。
- **上下文约束**：使用该技能时的边界条件。
- **执行路径**：拉起相关脚本或发起的具体操作。

## 参与贡献 (Contributing)

我们欢迎为本项目增加新的技能模块以扩展 Agent 的边界：
1. Fork 本仓库。
2. 在 `.claude/skills/` 目录下新建技能文件夹。
3. 编写 `SKILL.md` 并包含实现脚本。
4. 提交 Pull Request，并在描述中说明测试用例与适用场景。

## 开源协议 (License)

本项目基于 [MIT License](https://opensource.org/licenses/MIT) 开源。
