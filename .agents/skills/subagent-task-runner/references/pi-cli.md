# Pi CLI 后端

参考 agent-council 的 Pi 非交互调用方式。此处直接派发单个角色，执行任务循环。

## 探测与配置

1. 定位 `pi`：POSIX 用 `command -v pi`；PowerShell 用 `Get-Command pi`。
2. 运行 `pi --help` 和 `pi --list-models`，核对参数、思考强度与当前可用模型。
3. 在角色配置表中使用精确的 `provider/model`。思考强度须同时受本机 CLI 和所选模型支持；未知时先验证，再确认配置。

探测失败时保留错误输出，报告 Pi 后端不可用。模型清单表示可选配置；实际鉴权与连通性以调用结果为准。

## 文件与上下文

所有派发产物保存在 `scripts/workspace PLAN_FILE` 返回的目录下，包括 session 文件。每次调用分配独立的 prompt、events、stderr 文件，例如 `task-1-implement.prompt.md`、`task-1-implement.events.jsonl`。session 文件按阶段与角色命名为 `<阶段>-<角色>.session.jsonl`：`<阶段>` 为 `task-<N>` 或 `final`，`<角色>` 为 `implement`（实现与该任务的修复共用）、`review`、`rereview`、`fix`（仅最终阶段），例如 `task-1-implement.session.jsonl`、`task-1-rereview.session.jsonl`、`final-fix.session.jsonl`。文件统一使用 UTF-8。

按角色模板生成 prompt 正文，填入 brief、报告、review package 的绝对路径。补充适用的仓库指引路径，让 Pi 开始前读取。实现与修复保留模板中的报告文件契约。

实现者每个任务使用全新的 session 文件。修复与补充上下文使用该任务已有的 session 文件。每次审查使用独立的新 session 文件。把后端、模型、强度、session 路径和调用产物路径记录到账本。

## 子进程禁用后台任务

宿主如何启动 `pi` 不设限制：前台或后台、用什么等待与恢复工具由宿主决定，退出状态按「结果验收与恢复」判定。

约束落在子进程：实现与修复的命令带 `--exclude-tools` 与后台任务工具清单，使 pi 里的 agent 干活时不能把工作推给后台任务。

`BGTASK_TOOLS` 由 pi-background-tasks 的 `bg_*` / `fusion_*` 与 pi-subagents 的 `Agent` / `SubagentWorkflow` 组成，写成单个逗号分隔字符串：

```
bg_run,bg_run_pi_attested,bg_delegate,bg_result,bg_status,bg_logs,bg_kill,fusion_brainstorm,fusion_investigate,fusion_reason,fusion_research,fusion_validate,fusion_web_fetch,Agent,SubagentWorkflow
```

`Agent` 默认后台运行，`SubagentWorkflow` 始终后台，故一并禁用。本机扩展清单会变，调用前用 `pi --help` 与已装扩展核对工具名；`--exclude-tools` 按名称过滤，未知名称被忽略。

## 调用

以目标代码工作目录为 cwd。以下变量均在调用前按账本配置赋值，文件路径使用绝对路径。`promptFile` 是本次角色 prompt；`sessionFile` 是该角色的 session 文件。

PowerShell：

```powershell
$piExe = (Get-Command pi -ErrorAction Stop).Source
$piArgs = @(
  '-p', '--mode', 'json',
  '--model', $model, '--thinking', $thinking,
  '--session', $sessionFile
) + $roleArgs + @('--', "@$promptFile")
Push-Location -LiteralPath $codeRoot
try {
  & $piExe @piArgs 1> $eventsFile 2> $stderrFile
  $exitCode = $LASTEXITCODE
} finally {
  Pop-Location
}
```

使用 UTF-8 重定向的 PowerShell 版本（如 PowerShell 7）。POSIX Bash：

```bash
(
  cd "$code_root" || exit
  pi -p --mode json \
    --model "$model" --thinking "$thinking" \
    --session "$session_file" \
    "${role_args[@]}" -- "@$prompt_file" \
    > "$events_file" 2> "$stderr_file"
)
exit_code=$?
```

调用前按角色设置参数数组：

| 角色 | 参数 |
|------|-------|
| 实现、修复 | `--exclude-tools` 加 `BGTASK_TOOLS` 清单，其余保留后端完整工具集 |
| 任务审查、限定复审、最终审查 | `--no-extensions --no-skills --no-prompt-templates --no-context-files --tools read` |

PowerShell 用 `$roleArgs = @('--exclude-tools', $bgtaskTools)` 或上述审查参数组成的字符串数组；Bash 用 `role_args=(--exclude-tools "$bgtask_tools")` 或对应参数数组。审查角色的 `--tools read` allowlist 已排除后台任务。操作范围遵循用户授权及仓库指引。

Pi 内置工具缺少专用的 Git 只读入口，因此审查调用只开放 `read`。所需 Git 只读查询按主文档的角色工具权限交由 controller 执行，再将结果文件交给审查者。针对性测试也由 controller 执行。审查者把完整报告作为最终文本返回，由 controller 提取并写入本次审查报告文件。

运行期间保存进程句柄，通过宿主的后台执行和等待工具获取退出状态。超时或取消时先停止并确认原进程结束，再检查工作区与 session。后续恢复使用同一 session 和新的 prompt、events、stderr 文件。

## 结果验收与恢复

依次检查：

1. 进程退出码为 0。
2. stdout 每个非空行均能解析为 JSON。
3. 最后一个 `agent_end` 事件含 assistant 消息。
4. 该事件中最后一条 assistant 消息的 `stopReason` 为 `stop`。
5. 拼接该消息 `content` 中 `type == "text"` 的 `text`，结果须非空。

以上判定沿用 agent-council 的 `parse_pi_result` 规则。任一检查失败时保留日志，作为调用失败处理。禁止用部分流式文本标记任务完成。

实现者成功返回后，核对最终文本中的 `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`、报告文件和提交记录，再进入主流程的报告处理。审查者成功返回后，先落盘报告，再按审查契约判定 findings。

修复前确认账本中的 session 文件存在。向同一文件传入新的修复 prompt，并指向 findings 和报告文件。session 丢失时，以 brief、历史报告和 findings 启动新 session，记录替换原因。新任务与独立审查必须分配新的 session 路径。
