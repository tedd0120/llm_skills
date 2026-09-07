---
name: init
description: 新建项目时一键初始化 AGENTS.md 与 CLAUDE.md，配置语言规范、Git安全红线、docs/plans/ 阶段规划与实时状态跟踪、.prototype/ 原型规范及代码检索指引。
---

# 项目初始化（init）

新建项目时一键建立标准的 Agent 工作流配置。

## 核心规范

- **双文件单真源**：`CLAUDE.md` 引用 `@AGENTS.md`，所有规则收口在 `AGENTS.md`。
- **模板单真源**：规范正本存放在 `templates/`，脚本与说明均以此为准：
  - `templates/CLAUDE.md`：单真源入口声明。
  - `templates/AGENTS.md`：包含语言、Git 安全红线、`docs/plans/` 阶段与状态跟踪、`.prototype/` 原型目录、代码检索与 Skill 渐进式披露通用规则。

## 执行方式

优先运行配套脚本执行初始化：

```bash
# 默认对当前工作目录初始化
python <skill-dir>/scripts/init_project.py

# 指定目标项目路径
python <skill-dir>/scripts/init_project.py /path/to/project

# 强制覆盖已有文件
python <skill-dir>/scripts/init_project.py /path/to/project --force
```

## 执行流程

脚本按以下步骤处理目标项目：

1. **定位项目根目录**：以目标路径为起点，优先使用显式指定路径或包含 `.git` 的最近父目录。
2. **复制模板文件**：将 `templates/CLAUDE.md` 与 `templates/AGENTS.md` 写入项目根目录；已有文件默认跳过。
3. **创建规划目录**：建立 `docs/plans/` 目录并创建 `.gitkeep`。
4. **维护忽略规则**：检查根目录 `.gitignore`，缺失时追加 `.prototype/`。
