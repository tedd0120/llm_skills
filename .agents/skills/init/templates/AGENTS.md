# Agent 指引

## 语言

- 与用户交流及本仓库 Markdown 文档默认使用简体中文，参数名、命令、路径等专业名词保留英文。

## Git 操作

- 默认只允许 `git status`、`git diff`、`git log` 等只读查询。
- 改变本地或远端 Git 状态的操作（`git add`、创建或切换分支、`git commit`、`git push`、PR 等），必须由用户明确要求。
- `git restore`、`git reset`、`git clean`、`rebase` 等可能覆盖或丢失工作的操作，需要用户对具体目标作出明确授权。

## 任务规划与执行状态

- 规划文档写入 `docs/plans/`，命名格式为 `yyyyMMdd_HHmmss_*.md`。
- 新建独立 plan 无需遍历历史计划；续写、修订或承接已有计划时读取对应文件。
- 规划文档须划分执行阶段，并在创建时初始化各阶段及具体任务的执行状态（如 `[ ] 未开始`）。
- 执行 plan 过程中实时更新各阶段与子任务的执行状态，保持记录与代码实际进度一致。

## 原型产物

- 所有 prototype 产物放在仓库根目录的 `.prototype/{yyyyMMdd_HHmmss_主题}/` 下。
- 原型做成 standalone 单一入口、多方案同台展示；如无必要禁止启动后台服务。
- `.prototype/` 目录在 `.gitignore` 中忽略。

## 代码检索

- 仓库存在 `.codegraph/` 时，优先使用 CodeGraph 做聚合检索。

## Skill 规范

- 创建与编辑 Skill 遵循渐进式披露原则：主干流程写入 `SKILL.md`，细分场景规则独立存放于 `references/` 下按需读取。

