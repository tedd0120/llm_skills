# Agent 指引

## 语言

- 与用户交流及本仓库 Markdown 文档默认使用简体中文，参数名、命令、路径等专业名词保留英文。

## Git 操作

- 默认只允许 `git status`、`git diff`、`git log` 等只读查询。
- 改变本地或远端 Git 状态的操作（`git add`、创建或切换分支、`git commit`、`git push`、PR 等），必须由用户明确要求。
- `git restore`、`git reset`、`git clean`、`rebase` 等可能覆盖或丢失工作的操作，需要用户对具体目标作出明确授权。

## 任务规划与执行状态

- 规划文档写入任务工作区 `.work/<任务ID>/plan.md`。
- 新建独立 plan 无需遍历历史计划；续写、修订或承接已有计划时读取对应文件。
- 规划文档须划分执行阶段，并在创建时初始化各阶段及具体任务的执行状态（如 `[ ] 未开始`）。
- 执行 plan 过程中实时更新各阶段与子任务的执行状态，保持记录与代码实际进度一致。

## 工作区与产物目录

- 开发任务的过程材料按任务聚合在 `.work/<任务ID>/`，任务 ID 固定为 `{年月日}_{时分秒}_{任务主题}`：时间取自 `date +%Y%m%d_%H%M%S`，主题为 2–5 个小写英文单词以连字符连接。
- 任务目录按需创建子目录：计划 `plan.md`、原型 `prototype/`、临时材料 `scratch/`、子代理材料 `runner/`、验收证据 `evidence/`。微改动不建工作区。
- 跨任务复用的本机状态（测试账号、服务记录、登录态）放 `.local/<用途>/`。
- 原型做成 standalone 单一入口、多方案同台展示，交付评审后内容冻结，结论写入 `plan.md` 或 `evidence/conclusion.md`；如无必要禁止启动后台服务。
- `.work/` 与 `.local/` 在 `.gitignore` 中忽略。整理存量目录时使用 workspace-layout skill。

## 代码检索

- 仓库存在 `.codegraph/` 时，优先使用 CodeGraph 做聚合检索。

## Skill 规范

- 创建与编辑 Skill 遵循渐进式披露原则：主干流程写入 `SKILL.md`；不同场景与互斥分支在 `references/` 下各自独立建档，单次任务仅读取命中的分支文件。

