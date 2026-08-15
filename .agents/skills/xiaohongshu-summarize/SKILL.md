---
name: xiaohongshu-summarize
description: 小红书数据分析报告生成组件（内部，仅 scraper 调用）。读取 raw.json，按推荐选购、方案规划、事实核查或议题探索生成结构化 Markdown 报告。
---

# 小红书报告生成组件

> ⚠️ **内部组件** — 仅由 `xiaohongshu-scraper` 调用。

读取 `OUTPUT_DIR/raw.json`，按调用方传入的 `REPORT_TYPE` 生成报告并写入 `REPORT_FILE`。只生成草稿；emoji、URL 替换与发送仍由后续组件负责。

## 执行流程

1. 读取 raw.json，并提取 `search_time`、`posts`、`dedup`、`search_strategy` 与可选的 `divergence_path`。
2. 校验 `REPORT_TYPE`；若它与用户意图或数据明显不符，说明原因并改用推断值。缺省使用 `explore`。
3. **始终完整读取** [references/report-common.md](references/report-common.md)。
4. 按下表**只读取一本** runbook：

   | REPORT_TYPE | 必读文件 |
   |:--|:--|
   | `recommend` | [references/runbook-recommend.md](references/runbook-recommend.md) |
   | `plan` | [references/runbook-plan.md](references/runbook-plan.md) |
   | `factcheck` | [references/runbook-factcheck.md](references/runbook-factcheck.md) |
   | `explore` | [references/runbook-explore.md](references/runbook-explore.md) |

5. 先按 common 写搜索概览，再严格按命中的 runbook 写其余板块。
6. 写入调用方给定的 `REPORT_FILE`，不要自行推导文件名或执行后处理。

## 分析边界

- 使用 LLM 理解品牌、实体、观点、情绪与冲突；禁止调用脚本做文本分析、正则提取、词频统计或实体识别。
- 仅将帖子数、去重数、评论数、数值求和等确定性统计交给脚本或计算工具。
- 证据不足时明确写出，不得为了形成结论而抬高弱证据。
- 兼容旧数据：帖子无 `post_id` 时使用纯文本引用；评论为字符串时按正文读取，不假造作者、点赞或回复关系。

## 职责边界

只负责生成 `REPORT_FILE`。格式化、URL 占位符替换、任务验证和发送由 scraper 编排，禁止在本组件内代办。
