# Council Runner 参数与环境隔离规范

本文件定义调用 `scripts/run_council.py` 时的参数、权限沙箱与安全隔离机制。

## 常用参数

```text
python <skill-dir>/scripts/run_council.py \
  --workspace "<工作区路径>" \
  --run-dir "<workspace>/.agent-council/<run>" \
  --prompt-file "<run-dir>/prompt.txt" \
  --main-report-file "<run-dir>/reports/main-agent.md" \
  [--reviewer "pi:provider/model"] \
  [--reviewer "claude:model"] \
  [--available-claude-model "sonnet"] \
  [--thinking high] \
  [--claude-effort high] \
  [--max-parallel 5] \
  [--web-tools]
```

- `--thinking`：Pi thinking 等级（默认 `high`）。
- `--claude-effort`：Claude reasoning effort 等级（默认 `high`）。
- `--max-parallel`：最大并发数（默认 `5`）。
- `--web-tools`：当任务需要访问互联网时开启，为 Pi 挂载 `pi-web-access`，为 Claude 开放 `WebFetch,WebSearch`。

## 权限沙箱与环境隔离

- **只读约束**：Claude 以 `dontAsk` 权限运行，显式禁用 `Write`、`Edit`、`MultiEdit`，Git 仅放行只读查询命令。
- **配置隔离**：自动关闭全局会话记忆、slash commands、外部插件、hooks 及外部 `CLAUDE.md` 自动发现。
- **显式 Skill 链接**：prompt 中形如 `[$name](<path>/SKILL.md)` 的本地 skill 会被 runner 自动将所在目录加挂为只读目录（`--add-dir`）。

## 执行状态退出码

runner 执行完毕后 stdout 最后一行输出 JSON 摘要：

| status | 退出码 | 说明 |
|:---|---:|:---|
| `ready` | 0 | 至少两份 reviewer 报告生成成功，第一阶段完成 |
| `aborted` | 3 | 成功报告不足两份，未达会审门槛 |
| `error` | 2 | 参数配置或 CLI 调用前置错误 |
