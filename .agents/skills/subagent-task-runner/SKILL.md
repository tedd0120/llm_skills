---
name: subagent-task-runner
description: 按实现计划串行派发任务，支持内置 subagent 与 Pi CLI 后端，每任务后审查，全部完成后整体审查。
---

# Subagent Task Runner

按计划逐个派发独立 subagent 执行任务。每个任务：实现 → 审查 → 修复循环 → 完成。全部完成后做一次整体审查。

本文的 subagent 可通过当前 runtime 的内置工具或 Pi CLI 调用。按角色选择后端，可在同一计划中混用。

**核心原则：** 每任务一个新 subagent（隔离上下文）+ 任务审查（规格 + 质量）+ 最终整体审查 = 高质量、快迭代。

## 开场确认

执行前先向用户确认两件事，等用户回复后再开始准备阶段：

### 1. 分支策略

询问用户是否需要在独立分支上工作。展示当前分支状态（`git branch --show-current`），让用户选择：
- 在当前分支上直接工作
- 创建新的特性分支（让用户指定分支名，或根据计划名自动建议）

### 2. 后端、模型与思考强度配置

读完计划后，为三个角色各推荐一组模型与推理强度，让用户确认或调整。

先展示后端选项：`native`（当前 runtime 内置 subagent，默认）和 `pi`（本机 Pi CLI）。用户已指定的后端优先。选择或评估 `pi` 时，先阅读 [references/pi-cli.md](references/pi-cli.md)，完成 CLI 和模型探测，再生成角色建议。

当前 runtime 为 `codex`（大小写不敏感）且有 `native` 角色时，先阅读 [references/codex-radar.md](references/codex-radar.md)。按其中规则为 native 角色填入默认配置，展示「角色、后端、模型、推理强度、价格」；随后展示综合 IQ 与价格计算的 Top 5，列为「模型名、强度、IQ、价格」。该排名仅用于 native 角色。Pi 角色从 `pi --list-models` 的实时清单选择 `provider/model`，价格未知时标为「暂无数据」。

其他 runtime 根据整份计划的复杂度生成默认建议：

```
┌───────────────┬──────────┬──────────────┐
│ 角色           │ 模型      │ 思考强度      │
├───────────────┼──────────┼──────────────┤
│ 执行者         │ sonnet   │ high         │
│ 任务审查者      │ sonnet   │ high         │
│ 最终整体审查    │ opus     │ high         │
└───────────────┴──────────┴──────────────┘
```

在默认建议表中补齐每个角色的后端。执行者配置覆盖全部实现与修复任务，任务审查者配置覆盖任务审查与限定复审。用户可以按角色调整；用户主动指定时可按单个任务覆盖。确认后的后端、模型、思考强度和价格写入账本，后续派发严格按此执行。

## 行为准则

- 任务间不停下来问人。只有四种情况停下：不可逆操作、安全敏感操作、影响共享状态的副作用（push/merge/publish）、计划彻底无法前进。
- 遇到歧义和冲突自行裁决，在账本记录 `Ruling: <决定> — <原因> — <判断错误的代价>`。
- 工具调用之间最多说一句话——账本和工具结果承载记录。
- 所有中间产物（brief、report、diff package）通过文件传递，不贴进 prompt。

## 脚本运行时

`scripts/workspace`、`scripts/task-brief`、`scripts/review-package` 是 Bash 脚本。准备阶段开始时解析一次 Bash 可执行文件，后续脚本调用复用其绝对路径。

- POSIX shell：使用 `command -v bash`。
- PowerShell：先使用 `Get-Command bash.exe`。若命令不存在，从 `git.exe` 所在目录反推 Git for Windows 根目录，再依次检查 `bin\bash.exe` 和 `usr\bin\bash.exe`。也检查 `%ProgramFiles%\Git\bin\bash.exe` 与 `%LOCALAPPDATA%\Programs\Git\bin\bash.exe`。
- 找到解释器后继续当前步骤。仅在所有候选路径均不存在时报告缺少 Bash 运行时。

PowerShell 解析示例：

```powershell
$gitExe = (Get-Command git.exe -ErrorAction Stop).Source
$gitRoot = Split-Path (Split-Path $gitExe -Parent) -Parent
$candidates = @(
  (Get-Command bash.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
  (Join-Path $gitRoot 'bin\bash.exe'),
  (Join-Path $gitRoot 'usr\bin\bash.exe'),
  (Join-Path $env:ProgramFiles 'Git\bin\bash.exe'),
  (Join-Path $env:LOCALAPPDATA 'Programs\Git\bin\bash.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$bashExe = $candidates | Select-Object -First 1
if (-not $bashExe) { throw '找不到 Bash 运行时' }
```

将 `$skillRoot` 设为本 `SKILL.md` 所在目录。PowerShell 调用示例：`& $bashExe (Join-Path $skillRoot 'scripts\workspace') $planFile`。下文的 `scripts/...` 调用均通过已解析的 Bash 执行。

## 准备

1. 按开场确认的分支策略工作。
2. 运行 `scripts/workspace PLAN_FILE` 获取本计划的工作目录 `data/subagent-task-runner/<plan-basename>/`（git-ignored），用于存放账本、brief、report、review package 和 Pi 调用产物。恢复旧计划时先将对应 `.task-runner/<plan-basename>/` 迁入该目录；两处均存在时先核对账本再决定恢复来源。
3. 检查 `<workspace>/progress.md`：若首行指向本计划文件且有 `Task <N>: complete` 行，跳过已完成的任务；否则新建账本，首行 `# Ledger — plan: <plan file path>`。
4. 读一遍计划，为每个任务建一条 todo。若计划引用了 spec，也读——spec 是权威，计划是论证。
5. 开始前扫描任务间冲突：共享文件、接口矛盾、与全局约束的冲突。输出为表格写入账本。有冲突先裁决再动手。

账本是恢复地图：上下文压缩后，信任账本和 `git log`，不信自己的回忆。

## 模型选择

每个 subagent 按角色使用账本配置：实现与修复使用执行者配置，任务审查与限定复审使用任务审查者配置，最终整体审查使用最终整体审查配置。派发时显式指定，不要默认继承 controller 的模型。

如果某个任务的实际复杂度与预判不符（比如看似机械但实际需要多文件协调），提出升级建议，确认后将配置与偏差原因写入账本。

## 后端派发

- `native`：使用当前 runtime 的派发、等待和恢复工具，记录返回的 agent ID。
- `pi`：按 [references/pi-cli.md](references/pi-cli.md) 调用 CLI，记录 session 文件绝对路径。实现、修复、任务审查、限定复审和最终审查均使用该入口。命令禁用 pi 子进程的后台任务工具。
- 两个后端共用下文的角色模板和报告契约。模板中的 `Subagent` 外层表示派发元数据；Pi 的 prompt 文件只写 `prompt` 正文。
- 后端或模型不可用时记录阻塞原因；更换配置须取得用户确认。每次派发完成后再进入报告处理。

### 角色工具权限

执行者（实现与修复）使用 full tool，即所选后端提供的完整工具集（pi 后端按 [references/pi-cli.md](references/pi-cli.md) 去掉后台任务工具）。操作范围遵循用户授权和仓库指引。

任务审查、限定复审和最终审查仅使用 `read` 与 Git 只读命令。Git 查询限于 `status`、`diff`、`log`、`show`、`rev-parse`、`rev-list`、`merge-base`、`ls-files`，参数须用于读取；禁用外部 diff、textconv 和写文件参数。使用后端提供的受限命令工具执行这些查询。后端无法按命令约束 shell 时，由 controller 代执行查询并保存结果供审查者读取。针对性测试也由 controller 执行。

## 任务循环

**批量同质小任务：** 多个相同模式的小改动合成一个 dispatch。

### 1. 派发实现者

记录 `BASE = git rev-parse HEAD`。

- 运行 `scripts/task-brief PLAN_FILE N` 提取任务文本到文件。
- 派发 subagent，prompt 包含：
  1. 任务在项目中的位置（一句话）
  2. brief 文件路径（"读这个，这是你的需求"）
  3. 前置任务暴露的接口和决定
  4. 你对歧义的裁决
  5. report 文件路径和报告契约
- 实现者不得自行派发子 agent——审查由你在报告后派发。
- 不要并行派发多个实现者。
- 记录实现者的 agent identity——审查有 findings 时恢复此 agent 修复。

模板：[references/implementer.md](references/implementer.md)

### 2. 处理报告

| 状态 | 处理 |
|------|------|
| DONE | 生成 review package，派发审查者 |
| DONE_WITH_CONCERNS | 读 concerns，正确性/范围问题先处理再审查；观察性问题记录后直接审查 |
| NEEDS_CONTEXT | 补充信息，重新派发 |
| BLOCKED | 评估：补上下文 / 换更强模型 / 拆分任务 / 裁决计划错误后重新派发 |

实现者问问题时，完整回答，不急着催它开始。

### 3. 审查任务

运行 `scripts/review-package PLAN_FILE BASE HEAD`（BASE 是派发前记录的，不是 `HEAD~1`），用输出的 diff 文件路径派发审查者。审查者收到：brief 文件、report 文件、review package 文件，加上全局约束文本。

- 不要预判 findings——prompt 里不写"不要标记 X"。
- 不要让审查者重跑实现者已跑的测试。
- spec 合规和代码质量两个判定都不可省略。
- 审查者报告 ⚠️ 无法从 diff 验证的条目时，你自行确认——确认是真实缺口就进执行2。

模板：[references/reviewer.md](references/reviewer.md)

### 4. 执行2 与 评审2（评审未通过时）

一个任务就是一个阶段，固定形态：**执行 → 评审 → 执行2 → 评审2**。执行2 仅在评审未通过时发生。

评审报告 spec ❌ 或有 Critical/Important findings 时触发执行2。派发前记录 `FIX_BASE = git rev-parse HEAD`。恢复原实现者（或带 brief + report + findings 派新的），修复后运行 `scripts/review-package PLAN_FILE FIX_BASE HEAD`，派发 [references/re-reviewer.md](references/re-reviewer.md) 做评审2。

- 评审2 只验证 findings 是否修复 + 修复 diff 有无新问题。
- **不要自己在 controller 里修代码**——上下文保持干净，且自修跳过了审查。
- 一个阶段至多一次执行2。Minor findings 也留在账本，不在本阶段处理。

### 5. 收尾该阶段并强制推进

- 评审通过 → 账本记 `Task <N>: complete (commits <base7>..<head7>, review clean)`。
- 评审2 仍未通过 → **强制进入下一阶段**，不再修复。全部未解决 findings 逐条写入账本并标记 `carry-to-final`，附 `Ruling: 强制推进 — <理由> — <判断错误的代价>`。
- 账本中所有未解决条目（Minor 与 carry-to-final）统一在最终阶段解决。

标记 todo 完成，进入下一任务。

## 最终审查

所有任务完成后，运行 `scripts/review-package PLAN_FILE MERGE_BASE HEAD`（`MERGE_BASE = git merge-base main HEAD`），按账本中的最终整体审查配置派发整体代码审查。审查范围覆盖全部提交，并指向账本中所有 carry-to-final 与 Minor 条目。

最终阶段沿用同一形态：整体审查（评审）→ 执行2 → 评审2。

1. 派 **一个** 修复 subagent 处理全部 findings——整体审查 findings 加账本遗留条目（不要每条 finding 一个 fixer）。记录 `FIX_BASE = git rev-parse HEAD`。
2. 运行 `scripts/review-package PLAN_FILE FIX_BASE HEAD`，派发限定复审做评审2。
3. 评审2 后仍未解决的条目逐条裁决写入账本，并在收尾汇报中原样呈现——此处没有下一阶段可承接。

## 收尾

1. 收集账本中所有 `Ruling:` 行，在最终消息中列出"我做的裁决"，每条附判断错误的代价。这是用户看到你替他们做的决定的唯一途径。
2. 删除本计划的工作目录（`rm -rf <workspace>`），git 历史即记录。不动其他计划的目录。
3. 向用户汇报分支状态，让用户决定合并方式。

## 纪律

| 想法 | 现实 |
|------|------|
| "差不多符合 spec 了" | 审查发现 spec 缺口 = 没完成。进执行2；评审2 仍未过则写入账本并强制推进。 |
| "我自己修更快" | controller 修复污染上下文且跳过审查。恢复实现者。 |
| "修复很小，跳过复审" | 未审查的修复是回归的来源。修复后必须有限定复审。 |
| "让 pi 子进程自己后台跑" | pi 里的 agent 干活时不用后台任务；命令已用 `--exclude-tools` 移除这些工具。 |
| "这条 finding 明显是错的" | 裁决必须写入账本。禁止静默丢弃。 |
| "账本维护是开销" | 账本是上下文压缩后幸存的唯一记录。没有账本的 controller 重派了整个已完成序列。 |

## 示例

```
[准备：特性分支，workspace 初始化，读计划，建 todo]
[扫描计划冲突 → 账本]

Task 1: 安装钩子脚本
[task-brief → dispatch implementer with brief + report paths]
Implementer: DONE, 5/5 tests passing, committed
[review-package → dispatch reviewer]
Reviewer: Spec ✅, quality approved
[账本: Task 1: complete (commits a1b2c3d..d4e5f6a, review clean)]

Task 2: 恢复模式
[task-brief → dispatch implementer]
Implementer: DONE, 8/8 tests passing
[review-package → dispatch reviewer]
Reviewer: Spec ❌ (缺进度报告), Important (magic number)
[执行2: resume implementer with findings]
Implementer: fixed, 10/10 passing
[review-package FIX_BASE HEAD → dispatch re-reviewer]
评审2: 2 addressed, 0 open, no new breakage
[账本: Task 2: complete (commits b1c2d3e..e4f5a6b, review clean)]

Task 3: 并发写入
[执行 → 评审: Important findings]
[执行2 → 评审2: 1 条仍未解决]
[账本: Task 3: complete (commits c2d3e4f..a7b8c9d, 1 carry-to-final) + Ruling: 强制推进 — ...]

...

[所有任务完成]
[review-package MERGE_BASE HEAD → dispatch final reviewer (账本配置, 含账本遗留条目)]
Final reviewer: Sub-important findings + 1 carried item
[执行2: 一个 fixer 处理全部 → 评审2: 全部解决]

[删除 workspace，汇报裁决，让用户决定合并]
```
