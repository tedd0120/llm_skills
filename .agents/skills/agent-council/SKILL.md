---
name: agent-council
description: 通过 Pi CLI 与 Claude CLI 将用户任务 prompt 原样交给多个模型和主 Agent 独立完成并保存报告；收到用户下一条 prompt 后再按要求处理这些本地报告。
---

# Agent 会审（Agent Council）

采用双阶段流水线：
- **第一阶段（独立会审）**：主 Agent、Pi 与 Claude 独立完成同一条任务 prompt，各自生成并保存原始报告。
- **第二阶段（处理报告）**：收到用户的下一条 prompt 后，按其具体指令比对、汇总或裁决这些报告。

---

## 阶段一：独立会审执行

### 1. 任务 Prompt 原样提取

从当前用户 prompt 开头剥离 `$agent-council` 触发标记，将余下的完整任务内容原样写入 `.agent-council/<run-dir>/prompt.txt`（保持字符、换行与空白，禁止擅自修改）。

### 2. Reviewer 探测与确认

在调用 reviewer 前，**必须阅读 [references/reviewer-selection.md](references/reviewer-selection.md)** 执行模型探测与阻塞式确认：
- 探测本地 Pi 与 Claude 实时可用模型清单；
- 向用户展示当前默认配置与两端模型列表；
- 停在确认环节，等待用户回复后再继续。

### 3. 调用 Runner 并发执行

创建单层运行目录 `.agent-council/<run-dir>/`（名称格式 `YYYYMMDD_HHMMSS_<主题>`）。

查阅 **[references/runner-specification.md](references/runner-specification.md)** 获取参数与权限沙箱详情，调用后台 runner：

```bash
python .agents/skills/agent-council/scripts/run_council.py \
  --workspace "<工作区路径>" \
  --run-dir "<workspace>/.agent-council/<run-dir>" \
  --prompt-file "<run-dir>/prompt.txt" \
  --main-report-file "<run-dir>/reports/main-agent.md"
```

- **主 Agent 独立作答**：在 runner 运行期间，主 Agent 必须基于自身上下文独立完成任务；在 runner 提示 reviewer 调用完成后，一次性写入 `--main-report-file` 冻结。

### 4. 第一阶段完成判定

当且仅当以下条件满足时第一阶段结束：
- runner 退出且最后一行 JSON 摘要状态为 `ready`；
- 主 Agent 报告已写入 `reports/main-agent.md`；
- 至少两份 reviewer 报告生成完毕。

向用户汇报第一阶段已完成、展示报告清单，并请用户通过下一条 prompt 下发处理要求。

---

## 阶段二：按指令处理报告

收到用户的下一条 prompt 后，阅读 **[references/report-processing.md](references/report-processing.md)**：
- 将该 prompt 视为独立操作指令（如比对差异、提取共识、综合裁决）；
- 读取 `<run-dir>/reports/` 下所有原始报告执行分析；
- 派生产物默认保存在对应 `<run-dir>/` 目录下。
