---
name: xiaohongshu-fetch
description: 小红书数据抓取组件（内部，仅 scraper 调用）
---

# 小红书数据抓取组件

> ⚠️ **内部组件** — 本组件仅由 `xiaohongshu-scraper` 内部调用，**禁止用户单独调用**。

通过自动化浏览器（Playwright）抓取小红书上的帖子正文和评论区内容，输出为 `raw.json` 文件。支持固定关键词模式和多轮模式（发散 / 总分）的单轮抓取，支持跨轮去重。

## 命令行调用参数

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--keywords` | ✅ | 搜索关键词，多个关键词用逗号分隔 |
| `--max-posts` | ✅ | 帖子抓取上限（默认 100）|
| `--output` | ✅ | 输出文件**绝对路径**（如 `{OUTPUT_DIR}/raw.json`，禁止写入 skill 目录）|
| `--search-strategy` | ❌ | 搜索策略 JSON（固定模式使用）|
| `--seen-ids` | ❌ | 已见 ID 文件路径（多轮模式跨轮去重）|
| `--hyperlinks` | ❌ | 生成 `id_url_map.json`（供报告替换超链接）|
| `--safe-mode` | ❌ | 安全模式：增大延时规避风控（与 `--speed-mode` 互斥）|
| `--speed-mode` | ❌ | 极速模式：缩短随机延时快速抓取 |

*注：不传速度参数时为默认正常模式（平衡速度与安全）。*

## 调用示例

### 固定关键词模式

```bash
python .agents/skills/xiaohongshu-fetch/scripts/fetch_xhs.py \
  --keywords "关键词1,关键词2" \
  --max-posts 30 \
  --output "<OUTPUT_DIR>/raw.json"
```

### 多轮模式单轮抓取

```bash
python .agents/skills/xiaohongshu-fetch/scripts/fetch_xhs.py \
  --keywords "本轮关键词" \
  --max-posts 10 \
  --output "<OUTPUT_DIR>/raw_round_1.json" \
  --seen-ids "<OUTPUT_DIR>/seen_ids.txt"
```

## 输出产物规范

输出文件为标准 JSON，包含 `search_time`、`keywords`、`dedup`（含 `posts_scraped`、`posts_unique`、`dropped_duplicate`、`dropped_id_mismatch`）以及去重后的 `posts` 数组（帖子元数据与结构化评论列表）。
