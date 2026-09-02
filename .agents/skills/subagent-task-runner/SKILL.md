---
name: subagent-task-runner
description: 按实现计划串行派发 subagent 执行任务，每任务后审查，全部完成后整体审查
---

# Subagent Task Runner

按计划逐个派发独立 subagent 执行任务。每个任务：实现 → 审查 → 修复循环 → 完成。全部完成后做一次整体审查。

**核心原则：** 每任务一个新 subagent（隔离上下文）+ 任务审查（规格 + 质量）+ 最终整体审查 = 高质量、快迭代。

## 开场确认

执行前先向用户确认两件事，等用户回复后再开始准备阶段：

### 1. 分支策略

询问用户是否需要在独立分支上工作。展示当前分支状态（`git branch --show-current`），让用户选择：
- 在当前分支上直接工作
- 创建新的特性分支（让用户指定分支名，或根据计划名自动建议）

### 2. 模型与思考强度配置

读完计划后，根据各任务的复杂度，列出本次执行计划使用的 subagent 配置表，让用户确认或调整：

```
┌─────────────┬──────────┬──────────────┐
│ 角色         │ 模型      │ 思考强度      │
├─────────────┼──────────┼──────────────┤
│ 机械实现      │ sonnet   │ normal       │
│ 集成/多文件   │ sonnet   │ high         │
│ 任务审查      │ sonnet   │ high         │
│ 限定复审      │ sonnet   │ normal       │
│ 最终整体审查  │ opus     │ high         │
└─────────────┴──────────┴──────────────┘
```

表中的模型和思考强度是默认建议值。展示时，根据计划中每个任务的实际复杂度标注它会使用哪一行配置。用户可以按角色调整，也可以按单个任务覆盖。确认后的配置表写入账本，后续派发严格按此执行。

### 3. Codex 展示层推荐

仅当当前运行环境标识为 `codex`（大小写不敏感）时执行本节。

在展示 subagent 模型与思考强度配置表时，先读取 [Codex 雷达](https://codex-reset-radar.pages.dev/) 使用的 `data/intelligence-efficiency.json`。

- 候选取 `harness == "codex"` 且包含数值 `iq`、`average_price_usd` 的模型档位。
- 计划已限定模型族时按计划筛选；计划未限定时取接口中最新的 `gpt-*` 主模型系列。
- 性价比推荐取 IQ ≥ 95 中价格最低的档位。
- 均衡推荐取 IQ ≥ 100 中价格最低的档位。
- 上限推荐取 IQ 最高的档位。
- 候选不足三项时按 IQ 降序、价格升序补齐，并对重复档位去重。
- 价格使用 `average_price_usd`，单位为美元/基准任务。
- 日期使用 `source_updated_at`，只显示北京时间日期。

推荐行保持单行极简格式：

```text
Codex 推荐：<档位> IQ <分数> / $<价格> · <档位> IQ <分数> / $<价格> · <档位> IQ <分数> / $<价格> · 更新 <YYYY-MM-DD>
```

该行只提供展示参考，派发仍采用用户确认后的配置。接口读取失败或缺少更新日期时跳过推荐行并继续正常流程。

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
2. 运行 `scripts/workspace PLAN_FILE` 获取本计划的工作目录（git-ignored），用于存放账本、brief、report、review package。
3. 检查 `<workspace>/progress.md`：若首行指向本计划文件且有 `Task <N>: complete` 行，跳过已完成的任务；否则新建账本，首行 `# Ledger — plan: <plan file path>`。
4. 读一遍计划，为每个任务建一条 todo。若计划引用了 spec，也读——spec 是权威，计划是论证。
5. 开始前扫描任务间冲突：共享文件、接口矛盾、与全局约束的冲突。输出为表格写入账本。有冲突先裁决再动手。

账本是恢复地图：上下文压缩后，信任账本和 `git log`，不信自己的回忆。

## 模型选择

每个 subagent 的模型和思考强度严格按账本中记录的配置表执行。派发时显式指定，不要默认继承 controller 的模型。

如果某个任务的实际复杂度与预判不符（比如看似机械但实际需要多文件协调），可以临时升级，但需在账本记录偏差原因。

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

模板：[implementer.md](implementer.md)

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
- 审查者报告 ⚠️ 无法从 diff 验证的条目时，你自行确认——确认是真实缺口就进修复循环。

模板：[reviewer.md](reviewer.md)

### 4. 修复（如有）

审查报告 spec ❌ 或有 Critical/Important findings 时触发。Minor findings 记入账本留给最终审查。

**只做一轮修复：** 恢复原实现者（或带 brief + report + findings 派新的），修复后运行 `scripts/review-package PLAN_FILE FIX_BASE HEAD`，派发 [re-reviewer.md](re-reviewer.md) 做限定复审。

- 复审只验证 findings 是否修复 + 修复 diff 有无新问题。
- **不要自己在 controller 里修代码**——上下文保持干净，且自修跳过了审查。
- 复审后仍有未解决的 findings，逐条裁决写入账本：
  - 审查者有误 / 可争议 → park with ruling
  - 真实但无下游依赖 → park with ruling, 标记 deferred
  - 真实且 load-bearing → 裁决最小变更，carry 到下一任务的 dispatch

### 5. 完成任务

写入账本：
- `Task <N>: complete (commits <base7>..<head7>, review clean)`
- `Task <N>: complete (commits <base7>..<head7>, <K> parked)` （breaker 后）

标记 todo 完成，进入下一任务。

## 最终审查

所有任务完成后，运行 `scripts/review-package PLAN_FILE MERGE_BASE HEAD`（`MERGE_BASE = git merge-base main HEAD`），用最强模型派发整体代码审查。指向账本中的 deferred minors 和 parked findings。

如有 findings，派 **一个** 修复 subagent 处理全部（不要每条 finding 一个 fixer），然后做一次限定复审。残余 findings 逐条裁决写入账本。

## 收尾

1. 收集账本中所有 `Ruling:` 行，在最终消息中列出"我做的裁决"，每条附判断错误的代价。这是用户看到你替他们做的决定的唯一途径。
2. 删除本计划的工作目录（`rm -rf <workspace>`），git 历史即记录。不动其他计划的目录。
3. 向用户汇报分支状态，让用户决定合并方式。

## 纪律

| 想法 | 现实 |
|------|------|
| "差不多符合 spec 了" | 审查发现 spec 缺口 = 没完成。修复或到 breaker 裁决。 |
| "我自己修更快" | controller 修复污染上下文且跳过审查。恢复实现者。 |
| "修复很小，跳过复审" | 未审查的修复是回归的来源。修复后必须有限定复审。 |
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
[resume implementer with findings]
Implementer: fixed, 10/10 passing
[review-package FIX_BASE HEAD → dispatch re-reviewer]
Re-reviewer: 2 addressed, 0 open, no new breakage
[账本: Task 2: complete]

...

[所有任务完成]
[review-package MERGE_BASE HEAD → dispatch final reviewer (最强模型)]
Final reviewer: clean, deferred minors triaged — none block merge

[删除 workspace，汇报裁决，让用户决定合并]
```
