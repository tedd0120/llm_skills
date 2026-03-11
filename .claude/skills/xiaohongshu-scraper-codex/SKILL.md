---
name: xiaohongshu-scraper-codex
description: 小红书内容抓取与分析新架构入口（codex）
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书内容抓取 Skill（codex）

`xiaohongshu-scraper-codex` 是 codex 架构下的**唯一用户入口**。

它负责：
- 与用户完成澄清阶段
- 选择固定关键词模式或发散模式
- 展示执行进度
- 调用内部 orchestrator 完成登录、抓取、报告阶段调度和最终校验
- 将最终报告发送给用户

## 内部组件

- `scripts/orchestrator.py`：内部编排入口，负责目录初始化、认证、抓取、报告 handoff、报告定稿调用和任务状态收敛
- `xiaohongshu-fetch-codex`：内部抓取引擎，负责浏览器自动化采集
- `xiaohongshu-report-codex`：内部报告流水线，在同一 skill 边界内完成“LLM 草稿 + finalizer 定稿”
- `xiaohongshu-core-codex`：共享基础层，提供选择器、浏览器配置、认证状态和数据契约

## 报告阶段真实协议

报告阶段虽然只调用一个 `xiaohongshu-report-codex` 组件，但其内部实际分为两步：

1. **LLM 草稿**：LLM 读取 `raw.json`，按 `xiaohongshu-report-codex/SKILL.md` 生成完整 `report_draft.md`
2. **脚本定稿**：`build_report.py` 读取 `report_draft.md`，做链接替换、评论清理、分割线和固定元信息落盘，输出 `_index.md`

因此，orchestrator **不替代 LLM 完成报告归纳**；它只负责为报告阶段提供输入目录、检查前置文件，并在草稿准备好后调用 finalizer。

## orchestrator 行为

### 首次执行
首次执行时，orchestrator 会：
1. 创建输出目录与 `tasks.md`
2. 完成登录
3. 抓取并落盘 `raw.json`
4. 检查 `report_draft.md` 是否存在
5. 若草稿不存在，则打印明确 handoff 信息，提示先由 LLM 生成草稿
6. 若草稿已存在，则调用 report finalizer 生成 `_index.md`

### 继续报告阶段
如需在抓取完成后继续报告阶段，可复用已有目录：

```bash
python ".claude/skills/xiaohongshu-scraper-codex/scripts/orchestrator.py" --resume-dir "<output_dir>"
```

如草稿不在默认位置，可附加：

```bash
python ".claude/skills/xiaohongshu-scraper-codex/scripts/orchestrator.py" --resume-dir "<output_dir>" --draft "<draft_path>"
```

## 边界说明

- `xiaohongshu-scraper-codex` 是 codex 架构推荐入口
- 旧版 `xiaohongshu-scraper` 仍保留，作为兼容参考，不被覆盖
- codex 架构**不**把登录暴露为独立 skill；登录属于 orchestrator 内部认证步骤
- codex 架构**不**要求用户手动串联 fetch、summarize、formatter 等多个内部组件完成完整流程
- 但报告阶段内部仍必须遵循“LLM 先归纳，脚本再定稿”的协议

## 执行原则

1. 必须先完成澄清，再进入执行阶段
2. 用户确认后必须立即创建输出目录
3. orchestrator 必须维护阶段化任务清单与最终校验
4. 报告阶段对外只调用 `xiaohongshu-report-codex`
5. orchestrator 只能调度报告阶段，不能用脚本代替 LLM 生成整份语义报告

## 迁移说明

- 需要保留旧实现或核对历史行为时，参考旧版小红书 skills
- 需要采用新架构时，优先使用 `xiaohongshu-scraper-codex`
- 若 `tasks.md` 中显示“生成报告”只有一项，应理解为该项内部包含“LLM 草稿 + finalizer 定稿”两步
