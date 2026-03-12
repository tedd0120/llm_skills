---
name: xiaohongshu-fetch-codex
description: 小红书数据抓取引擎（codex 内部组件）
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书数据抓取组件（codex）

> ⚠️ **内部组件** — 本组件由 `xiaohongshu-scraper-codex` 的 orchestrator 调用，不作为完整流程的用户入口。

`xiaohongshu-fetch-codex` 负责浏览器自动化采集：
- 固定模式抓取
- 发散模式中的单轮抓取
- `seen_ids` 跨轮去重
- 生成轮次原始数据与最终合并所需输入

## 输入边界

- 接收 orchestrator 已确认好的参数执行抓取
- 不负责澄清阶段
- 不负责多轮编排决策
- 不负责最终报告生成
- 复用 `xiaohongshu-core-codex` 中的共享选择器、浏览器配置和认证状态解析逻辑

## 与 orchestrator 的关系

- `fixed` 模式下，通常被调用一次并直接产出 `raw.json`
- `divergent` 模式下，由 orchestrator 多次调用，每轮产出 `raw_round_N.json`
- orchestrator 负责轮数、配额拆分、结果合并和轮次元数据落盘
- 抓取层继续复用 `max_posts`、关键词配额和 `seen_ids` 去重能力
