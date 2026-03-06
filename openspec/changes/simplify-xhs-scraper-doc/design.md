## 上下文

`xiaohongshu-scraper` 是小红书爬虫系统的编排层 skill，负责协调 `xiaohongshu-login`、`xiaohongshu-fetch`、`xiaohongshu-summarize`、`xiaohongshu-formatter` 四个子 skills。

当前 SKILL.md 文件存在以下问题：
- 801 行文档中约 72% 内容冗余或越界
- 包含了属于子 skill 的完整报告模板（已在 `xiaohongshu-summarize` 中定义）
- 「核心要求清单」与「重要提醒」章节重复
- CLI 命令示例与 `xiaohongshu-fetch` 重复

## 目标 / 非目标

**目标：**
- 将 SKILL.md 精简至约 220 行
- 明确编排层职责边界，子 skill 仅用一句话概括并引用其文档
- 消除跨文件和文件内重复内容

**非目标：**
- 不改变任何运行时行为
- 不修改子 skill 的文档
- 不调整功能规范

## 决策

### 决策 1：保留澄清阶段详细说明

**选择**：保留澄清阶段的详细流程说明（约 100 行）

**理由**：澄清阶段是编排层的核心职责，涉及用户交互和模式选择逻辑，需要详细的操作指南。

**替代方案**：精简为概要 → 否决：澄清阶段交互复杂，概要不足以指导 Agent 正确执行。

### 决策 2：删除报告模板，改为引用 summarize skill

**选择**：完全删除 SKILL.md 中的报告模板章节

**理由**：`xiaohongshu-summarize` skill 已包含完整报告模板，编排层无需重复。引用方式：「调用 xiaohongshu-summarize（详见其 SKILL.md）生成报告」。

### 决策 3：合并「核心要求清单」与「重要提醒」

**选择**：保留「核心要求清单」，删除「重要提醒」章节

**理由**：核心要求清单是表格形式的汇总，更清晰；「重要提醒」是相同内容的重复列表形式。

### 决策 4：删除 CLI 基础用法章节

**选择**：删除 CLI 基础用法章节

**理由**：具体命令示例已在 `xiaohongshu-fetch` 的 SKILL.md 中定义，编排层只需说明「调用 xiaohongshu-fetch（详见其 SKILL.md）执行抓取」。

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| Agent 可能不查看子 skill 文档 | 在编排层明确标注「详见其 SKILL.md」，并使用引用链接 |
| 信息分散可能导致查找不便 | 在编排层保留概览性的流程图，子 skill 负责细节 |
| 删除内容后可能需要恢复 | Git 版本控制保留历史记录 |
