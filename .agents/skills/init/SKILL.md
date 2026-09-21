---
name: init
description: 新建项目时一键初始化 AGENTS.md 与 CLAUDE.md，或对存量项目进行查漏补缺。配置语言规范、Git安全红线、阶段规划与实时状态跟踪、.work/ 任务工作区与产物目录、代码检索及 Skill 渐进式披露指引。
---

# 项目初始化与规范对齐（init）

支持两种工作场景：
1. **全新项目初始化**：一键生成标准单真源双文件（`CLAUDE.md` 与 `AGENTS.md`）及工程基础设施。
2. **存量项目查漏补缺**：当已有 `AGENTS.md` 或 `CLAUDE.md` 时，严格遵循非侵入原则，仅追加缺失的通用规则板块，完整保留既有业务规范。

## 核心规范

- **双文件单真源**：`CLAUDE.md` 引用 `@AGENTS.md`，所有规则收口在 `AGENTS.md`。
- **模板单真源**：标准正本存放在 `templates/`：
  - `templates/CLAUDE.md`：单真源入口声明。
  - `templates/AGENTS.md`：包含 6 项通用规则（语言、Git 安全红线、`.work/<任务ID>/plan.md` 阶段与状态跟踪、`.work/` 任务工作区与 `.local/` 本机状态、代码检索、Skill 渐进式披露与文件级隔离）。

## 执行方式

优先运行配套脚本执行初始化或查漏补缺：

```bash
# 默认对当前工作目录进行初始化或查漏补缺
python <skill-dir>/scripts/init_project.py

# 指定目标项目路径
python <skill-dir>/scripts/init_project.py /path/to/project

# 强制覆盖已有文件（仅在需要彻底重置项目规则时使用）
python <skill-dir>/scripts/init_project.py /path/to/project --force
```

## 两种场景流转

### 场景 1：全新项目初始化（未检测到 AGENTS.md / CLAUDE.md）

1. **定位项目根目录**：以目标路径或向上找 `.git` 确定项目根。
2. **复制标准文件**：将 `templates/CLAUDE.md` 与 `templates/AGENTS.md` 写入项目根目录。
3. **维护忽略规则**：在根目录 `.gitignore` 中追加 `.work/` 与 `.local/`。

### 场景 2：存量项目查漏补缺（已存在 AGENTS.md 或 CLAUDE.md）

查阅 **[references/patch-audit.md](references/patch-audit.md)** 进行增量比对与补齐：
1. **`CLAUDE.md` 单真源核对**：检查是否包含 `@AGENTS.md` 引用，缺失时前置注入引用声明。
2. **`AGENTS.md` 规则核对**：比对 6 大标准通用板块，仅将缺失的板块追加至文件末尾，原样保留既有业务配置。既有规则仍使用 `docs/plans/`、`.prototype/` 等旧产物目录时，不追加工作区相关板块，提示改用 workspace-layout skill 迁移。
3. **忽略规则补齐**：`.gitignore` 缺少 `.work/`、`.local/` 时追加。
