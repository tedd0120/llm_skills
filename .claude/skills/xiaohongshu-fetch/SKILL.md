---
name: xiaohongshu-fetch
description: 小红书数据抓取组件（内部，仅 scraper 调用）
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书数据抓取组件

> ⚠️ **内部组件** — 本组件仅由 `xiaohongshu-scraper` 内部调用，**禁止用户单独调用**。

通过自动化浏览器（Playwright）抓取小红书上的帖子正文和评论区内容，输出为 raw.json 文件。

---

## 功能

- 接收明确的搜索参数执行抓取
- 支持固定关键词模式和发散模式单轮抓取
- 输出标准格式的 JSON 数据文件
- 支持跨轮去重（通过 `--seen-ids` 参数）

---

## 参数

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--keywords` | ✅ | 搜索关键词，多个关键词用逗号分隔 |
| `--max-posts` | ✅ | 帖子上限（硬上限 100）|
| `--output` | ✅ | 输出文件路径（如 `data/xiaohongshu/.../raw.json`）|
| `--search-strategy` | ❌ | 搜索策略 JSON（固定模式使用）|
| `--seen-ids` | ❌ | 已见 ID 文件路径（发散模式去重使用）|
| `--safe-mode` | ❌ | 安全模式：延迟增大 2.5-3x + 随机阅读停顿 |
| `--speed-mode` | ❌ | 极速模式：去除所有延时（优先级高于 safe-mode）|

---

## 使用方式

由 `xiaohongshu-scraper` 在完成澄清阶段后自动调用。

### 固定关键词模式

```bash
python .claude/skills/xiaohongshu-fetch/scripts/fetch_xhs.py \
  --keywords "关键词1,关键词2,关键词3" \
  --max-posts 30 \
  --search-strategy '[{"keyword":"关键词1","posts_count":10,"intent":"获取整体推荐趋势"}]' \
  --output "data/xiaohongshu/YYYYMMDD_HHmmSS_主题/raw.json"
```

### 发散模式单轮

```bash
python .claude/skills/xiaohongshu-fetch/scripts/fetch_xhs.py \
  --keywords "本轮关键词" \
  --max-posts 10 \
  --output "data/xiaohongshu/YYYYMMDD_HHmmSS_主题/raw_round_1.json" \
  --seen-ids "data/xiaohongshu/YYYYMMDD_HHmmSS_主题/seen_ids.txt"
```

---

## 速度模式

| 模式 | 参数 | 行为 |
|------|------|------|
| 安全模式 | `--safe-mode` | 延迟增大 2.5-3x + 10% 概率随机阅读停顿(5-15s) |
| 正常模式 | (默认) | 内置随机延时，平衡速度与安全 |
| 极速模式 | `--speed-mode` | 跳过所有延迟（优先级高于 safe-mode） |

---

## 输出格式

输出的 JSON 文件包含以下字段：

| 字段 | 说明 |
|------|------|
| `search_time` | 执行时间 |
| `keywords` | 搜索关键词列表 |
| `posts` | 帖子数组，每个帖子包含：note_id, url, title, content, author, date, likes, collects, comments_count, comments |
