---
name: workspace-layout
description: 工作区整理：把仓库里散落的计划、原型、临时文件、子代理材料和本机状态按“正式资产 / 任务工作区 .work / 本机状态 .local / 程序自管”四层归位，并重审 .gitignore。先扫描、可疑目录先问用户，再出方案、经确认后迁移。用户说“整理工作区”“目录太乱”“规范产物目录”“哪些该进 gitignore”时使用。
---

# 工作区整理（workspace-layout）

调用即对当前仓库执行整理。目标布局以 [templates/artifacts.md](templates/artifacts.md) 为唯一标准：四层归属、`.work/<任务ID>/` 任务工作区、任务 ID `{年月日}_{时分秒}_{任务主题}`、按规模决定是否建目录。

流程有两道闸门：**问询闸门**（可疑目录得到用户答复前不定归属）和**执行闸门**（方案得到用户确认前不移动、不删除、不改文件）。闸门之前只读，唯一的写入是本次整理自己的任务目录。

## 1. 定位

- 工作区根取 `git rev-parse --show-toplevel`；不是 Git 仓库时以用户给出的目录为根，并在方案中注明无法做 Git 相关检查。
- 读取 `AGENTS.md`、`CLAUDE.md` 及其引用的产物、测试、部署文档，记下其中写死的目录约定。
- 执行 `date +%Y%m%d_%H%M%S` 得到本次任务 ID `<时间>_workspace-layout`，建 `.work/<任务ID>/evidence/`。

完成标准：已知根目录、现有约定清单、本次任务目录。

## 2. 扫描

```bash
python3 -B <skill>/scripts/scan_workspace.py --root <根> > .work/<任务ID>/evidence/scan-before.json
python3 -B <skill>/scripts/scan_workspace.py --root <根> --format md > .work/<任务ID>/evidence/scan-before.md
git -C <根> status --porcelain --ignored > .work/<任务ID>/evidence/git-status-before.txt
```

扫描器只读，列出根层级全部条目和深层中的产物类目录，给出 `layer_guess`、Git 跟踪与未忽略文件数、命中的忽略规则、引用它的已跟踪文件、进程占用、`questions`（需问用户）与 `actions`（待处理）。分类依据是 [references/known-paths.json](references/known-paths.json)；遇到新的常见模式时补进该表。

完成标准：三份结果已落盘，并已读完 markdown 版。

## 3. 分类与问询（问询闸门）

读 [references/classification.md](references/classification.md)，按其判定顺序处理每条扫描结果。对 `ask`、`unknown` 及带 `questions` 的条目，先自行查看内容与引用处上下文，再合并成一轮问用户，每条附证据和推荐归属。

完成标准：每条带 `questions` 的条目都有用户确认的归属；确认前不进入第 4 步。

## 4. `.gitignore` 分析

读 [references/gitignore.md](references/gitignore.md)，逐项执行其“必查项”，按归属生成新的分节 `.gitignore` 草案，并列出每条增删改的理由。已跟踪文件需移出版本库时，列为待用户授权项。

完成标准：必查项全部有结论；每个非 `asset` 条目都被规则覆盖；没有 `asset` 被规则命中。

## 5. 方案（执行闸门）

写 `.work/<任务ID>/plan.md`，`Status: 进行中`，阶段与子任务以 `[ ] 未开始` 初始化：

1. 归属表：路径、归属、依据（扫描/用户确认）、处置。
2. 迁移清单：源 → 目标任务 ID 与子目录、占用情况、需更新的引用。
3. `.gitignore` 变更草案与理由。
4. 文档：把 `templates/artifacts.md` 填好占位符后写入仓库的 agent 文档目录（默认 `docs/agents/artifacts.md`）；把 `templates/agents-snippet.md` 并入 `AGENTS.md`（没有时并入 `CLAUDE.md`，都没有时问用户），替换其中旧的计划、原型、临时目录条目。
5. 代码改动：硬编码旧路径的测试与脚本。
6. 可选：安装 `scripts/artifacts.py` 到仓库工具目录。
7. 验收项。

向用户汇报方案摘要并等待确认。Git 写操作（`git rm --cached`、提交等）只在用户明确要求时执行。

完成标准：用户确认了方案，或给出修改意见并已改进方案后再确认。

## 6. 执行

按 [references/migration.md](references/migration.md) 逐项执行迁移、更新引用、改代码、写文档与 `.gitignore`，每完成一项在 `plan.md` 勾选。有占用或校验不一致的项跳过并标注原因，不强行处理。

模板占位符按目标仓库实情填写：`{{ASSET_PATHS}}`、`{{PROGRAM_ROWS}}`、`{{LOCAL_ROWS}}` 用归属表中的实际路径；`{{BUSINESS_POINTER}}` 指向仓库已有的业务产物权威文档，没有时删去；`{{PROMOTION_TARGETS}}`、`{{TOOLS_DIR}}` 写仓库实际的术语表、ADR、说明文档与工具目录；`{{SPEC_PATH}}` 为规范文档相对指引文件的路径；`{{ID_TOOL_NOTE}}` 在安装清理工具时写“；清理工具按此校验”，否则删去；`{{LEGACY_DIRS}}`、`{{LEGACY_ROWS}}` 只列本仓库实际迁移过的旧目录，没有时删去该节；未安装清理工具时 `{{CLEANUP_SECTION}}` 写手动清理步骤，安装后写工具命令。填完后全文检查不再残留 `{{`。

## 7. 验收

- 重新扫描，输出 `evidence/scan-after.md`：不再有 `legacy` 条目、不再有“产物未被忽略”动作；剩余 `questions` 均已在方案中有答复。
- 执行 `git status --porcelain --ignored`，与整理前对比，每处差异可解释。
- 改过代码时运行受影响的测试，并确认运行后旧目录没有被重建。
- 在 `evidence/acceptance.md` 记录命令、时间、结果与代码版本；`plan.md` 标 `Status: 完成`，把未处理项列为范围外。

完成标准：上述四项全部满足，最终向用户汇报迁移结果、`.gitignore` 变化、跳过项与仍需用户决定的事项。

## 与 subagent-task-runner 的衔接

新布局下所有计划都名为 `plan.md`。所用 subagent-task-runner 的 `scripts/workspace` 需支持“计划名为 `plan.md` 时工作目录为同级 `runner/`”；不支持时在方案中列为风险：多个任务会共用同一个 `.task-runner/plan/`。
