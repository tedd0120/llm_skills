---
name: init
description: 新建项目时初始化 AGENTS.md、CLAUDE.md 与 .gitignore，或对存量项目查漏补缺。配置语言与措辞、沟通与方案设计、编码与文件操作、Git 操作、阶段规划与实时状态跟踪、.work/ 任务工作区与产物目录、测试剃刀原则、代码检索及 Skill 渐进式披露指引。
---

# 项目初始化与规范补全（init）

读取 [templates/AGENTS.md](templates/AGENTS.md) 作为通用规范正本，使用文件读写与编辑工具完成目标项目的初始化或增量补全。

## 全新项目初始化

目标项目根目录不存在 `AGENTS.md` 与 `CLAUDE.md` 时：

1. 将 [templates/AGENTS.md](templates/AGENTS.md) 写入根目录 `AGENTS.md`。
2. 在根目录创建 `CLAUDE.md`，写入 `@AGENTS.md`。
3. 检查根目录 `.gitignore`，缺失 `.work/` 或 `.local/` 时追加。

## 存量项目查漏补缺

目标项目根目录已存在 `AGENTS.md` 或 `CLAUDE.md` 时，保留既有业务配置与自定义规则，按以下顺序补全：

1. **`CLAUDE.md` 单真源引用**：若缺少 `@AGENTS.md`，在 `CLAUDE.md` 顶部前置插入 `@AGENTS.md`；若 `CLAUDE.md` 包含独立业务规则，将其迁移合并至 `AGENTS.md` 后保留 `@AGENTS.md` 单行引用。
2. **`AGENTS.md` 规则比对与补齐**：对照 [templates/AGENTS.md](templates/AGENTS.md) 的 9 个板块逐项核对既有 `AGENTS.md`：
   - 既有板块缺少模板中的具体规则条文时，将缺失条文补充至对应板块。
   - 完全缺失的板块追加至 `AGENTS.md` 末尾。
   - 既有 `AGENTS.md` 仍使用 `docs/plans`、`.prototype/`、`.prototypes/`、`.tmp/` 等旧产物目录时，跳过 `任务规划与执行状态` 与 `工作区与产物目录` 两个板块，提示用户使用 `workspace-layout` 技能迁移。
3. **`.gitignore` 规则补齐**：缺失 `.work/` 或 `.local/` 时追加至文件末尾。
4. **变更回显**：向用户列出本次保留的既有板块与新增补齐的板块或条文。
