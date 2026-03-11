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
- 固定关键词模式抓取
- 发散模式单轮抓取
- `seen_ids` 跨轮去重
- 生成 `raw.json` 与可选的 `id_url_map.json`

## 输入边界

- 接收明确参数执行抓取
- 不负责澄清阶段
- 不负责最终报告生成
- 复用 `xiaohongshu-core-codex` 中的共享选择器、浏览器配置和认证状态解析逻辑

## 与旧版关系

- 旧版 `xiaohongshu-fetch` 保留作为兼容参考
- codex 版优先消除重复基础脚本，不再复制共享实现
