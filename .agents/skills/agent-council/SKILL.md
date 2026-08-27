---
name: agent-council
description: 通过 Pi CLI 与 Claude CLI 将用户任务 prompt 原样交给多个模型和主 Agent 独立完成并保存报告；收到用户下一条 prompt 后再按要求处理这些本地报告。
---

# Agent 会审（Agent Council）

第一阶段让主 Agent、Pi 与 Claude 独立完成同一条 user prompt，并保存各自的原始报告。收到用户下一条 prompt 后，再按该指令处理这些报告。

## 任务 prompt 原样传递

技能调用标记只负责路由。先从当前 user prompt 开头移除 `$agent-council` 或 Codex 展开的 `[$agent-council](.../SKILL.md)`，将余下的用户任务逐字写入本次 `.agent-council/<run>/prompt.txt`。runner 会拒绝仍带调用标记的文件。

将 `prompt.txt` 的完整内容作为每个 Pi 或 Claude 调用的 stdin，保持字符、换行、顺序和尾随空白。CLI 参数限定为模型、工具和运行方式的现有选项。

若用户原文依赖当前 prompt 之外的早先上下文，说明缺失内容并请用户给出一条自包含 prompt，收到后再调用模型。

## 每次调用的启动检查

按顺序完成以下步骤，全部完成后才调用 reviewer：

1. 用 `git rev-parse --show-toplevel` 解析工作区根；不在 Git 工作树中则使用当前目录。
2. 检查根目录下的 `.agent-council/`；不存在则创建。
3. 检查 `.agent-council/default-models.txt`；不存在则创建为 0 字节空文件。
4. 读取默认模型配置。格式为每个非空行一个 reviewer ID：`pi:provider/model` 或 `claude:model`。保留文件中的顺序。
5. 实际执行 `pi --list-models`，将本次输出作为当前 Pi 可用模型清单。
6. 在调用 reviewer 前向用户逐项列出：
   - 默认使用模型；配置为空时明确写“未配置”。
   - 本次 `pi --list-models` 返回的全部可用模型。
   - 本次实际请求的 reviewer 名单。

runner 会再次执行同样的目录、配置和 Pi CLI 检查，并在 stderr 与最终 JSON 摘要中返回 `default_models`、`available_pi_models` 和 `default_models_config`。以本次 CLI 输出为准。

默认使用 `.agent-council/default-models.txt` 中的名单。用户在当前 prompt 明确指定 reviewer 时，以用户指定名单覆盖配置，同时仍列出配置默认值与全部 Pi 可用模型。配置为空且用户未指定 reviewer 时，保持文件为空并请用户选择至少两个 reviewer，收到选择后再调用。

## 调用 runner

在 `.agent-council/` 内创建唯一的单层运行目录 `<run-dir>`，名称使用 `YYYYMMDD_HHMMSS_<主题>`，冲突时追加数字后缀。在调用 runner 前写入：

- `<run-dir>/prompt.txt`：当前 user prompt 的原样 UTF-8 内容。
- `<run-dir>/reports/main-agent.md`：传给 runner 的预留路径；runner 启动时创建 `reports/`，该文件由主 Agent 稍后写入。

本技能的临时文件、暂存输出、输入记录、主 Agent 报告和最终产物全部位于 `.agent-council/`。

从本 `SKILL.md` 所在目录定位 `scripts/run_council.py`：

```text
python <skill-dir>/scripts/run_council.py \
  --workspace "<工作区或仓库路径>" \
  --run-dir "<workspace>/.agent-council/<run>" \
  --prompt-file "<run-dir>/prompt.txt" \
  --main-report-file "<run-dir>/reports/main-agent.md"
```

用户覆盖默认名单时，按用户给出的顺序重复传入：

```text
--reviewer "pi:provider/model"
--reviewer "claude:model"
```

可用参数：

- `--thinking <level>`：Pi thinking，默认 `high`。
- `--claude-effort <level>`：Claude effort，默认 `high`。
- `--max-parallel <n>`：最大并发数，默认 `5`。
- `--web-tools`：当用户任务要求访问 URL 或检索网络资料时启用。runner 实际执行 `pi list` 定位已安装的 `pi-web-access`，为 Pi 开放 `web_search,source_check,fetch_content,get_search_content`；Claude 开放 `WebFetch` 并使用 `auto` 权限模式。Pi 扩展缓存、仓库克隆以及 Claude 与 Pi 的系统临时目录位于本次 `<run-dir>/`。

至少请求两个 reviewer。Pi 模型必须出现在本次 `pi --list-models` 输出中；runner 可在同一 provider 内按既定优先级替换不可用模型，并如实披露替换。Claude 模型由 Claude CLI 调用时校验。每次尝试默认超时 3600 秒，失败重试一次。

runner 使用 Pi JSONL 与 Claude JSON 读取终止状态。只有正常结束且包含最终回答的调用记为成功；长度上限、未完成工具调用、空回答和结构化输出错误进入重试。重试仍失败时，报告保留完整原始 stdout 与 stderr。

后台启动 runner。确认 reviewer 调用开始后，主 Agent 立即独立完成用户原始任务，并将完整结果暂时保留在自身上下文中。runner 提示全部 reviewer 调用完成后，主 Agent 在读取 reviewer 输出前把结果一次性写入 `--main-report-file`，视为冻结。

Pi 调用始终开放 `read,grep,find,ls`，并通过 CLI 参数关闭会话、自动扩展发现、技能、prompt 模板和上下文文件；启用 `--web-tools` 时只显式加载 `pi-web-access`。Claude 调用始终开放 `Read,Grep,Glob`，使用独立 reviewer system prompt 只输出完整答案，不模拟或转录工具调用。CLI 参数同时启用安全模式并关闭会话持久化、slash commands、项目技能、插件、hooks、MCP 与 `CLAUDE.md` 自动发现；联网任务另外开放 `WebFetch`。

runner 校验 `<run-dir>` 是 `.agent-council/` 的直接子目录，并校验 prompt 与主 Agent 报告路径都在本次目录内。reviewer 调用期间，runner 只在进程内存中保留各模型输出；全部调用结束后才统一写入 `<run-dir>/reports/`。主 Agent 此后再写自己的报告。stdout 最后一行是 JSON 摘要：

| status | 退出码 | 处置 |
|---|---:|---|
| `ready` | 0 | 至少两份 reviewer 输出成功，第一阶段报告已就绪 |
| `aborted` | 3 | 成功输出不足两份；向用户报告未达到多模型会审门槛 |
| `error` | 2 | 参数、环境、reviewer 选择或 CLI 前置错误；说明后处理 |

## 第一阶段结束

runner 结束后只读取最后一行 JSON 摘要，以确认状态和文件路径。第一阶段在以下条件全部满足时结束：

- 主 Agent 与本次请求的全部 reviewer 都已结束。
- 主 Agent 的结果已写入 `<run-dir>/reports/main-agent.md`。
- 每个成功或失败的 reviewer 都有对应的本地报告记录。

随后提示用户第一阶段已经完成，提供运行目录、成功/失败 reviewer 和报告文件列表，并请用户用下一条 prompt 指定报告处理操作，然后结束当前回合。

## 按下一条 prompt 处理报告

用户下一条 prompt 到达后，将它视为一个新的、独立的处理指令。使用当前对话最近一次第一阶段运行目录中的本地报告，执行该 prompt 明确要求的操作，例如读取、比较、汇总、筛选、转换或生成派生文档。用户明确要求重新调用模型时，开始新一轮第一阶段。

把处理报告产生的临时文件和派生文档写在对应 `<run-dir>/` 内，除非用户明确指定该目录中的其他位置。若当前对话存在多个可能的运行目录或用户指代不清，先确认目标目录。

第一阶段的产物限于原始报告。后续操作以用户的新 prompt 授权范围为准，并保留历史 `.agent-council/` 与 `.pi-council/` 目录。
