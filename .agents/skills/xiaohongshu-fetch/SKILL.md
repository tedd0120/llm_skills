---
name: xiaohongshu-fetch
description: 小红书数据抓取组件（内部，仅 scraper 调用）
---

# 小红书数据抓取组件

> ⚠️ **内部组件** — 本组件仅由 `xiaohongshu-scraper` 内部调用，**禁止用户单独调用**。

通过自动化浏览器（Playwright）抓取小红书上的帖子正文和评论区内容，输出为 raw.json 文件。支持固定关键词模式和发散模式单轮抓取，支持跨轮去重。

## 参数

| 参数 | 必填 | 说明 |
|------|:----:|------|
| `--keywords` | ✅ | 搜索关键词，多个关键词用逗号分隔 |
| `--max-posts` | ✅ | 帖子上限（无上限，默认 100）|
| `--output` | ✅ | 输出文件**绝对路径**（`{OUTPUT_DIR}/raw.json`；OUTPUT_DIR 约定见 scraper 的 SKILL.md，禁止写入 skill 目录）|
| `--search-strategy` | ❌ | 搜索策略 JSON（固定模式使用）|
| `--seen-ids` | ❌ | 已见 ID 文件路径（发散模式跨轮去重）|
| `--hyperlinks` | ❌ | 生成 `id_url_map.json`；`post_id` 与 `url` 无论是否启用都会写入 raw.json |
| `--safe-mode` | ❌ | 安全模式：延迟增大 2.5-3x + 10% 概率随机阅读停顿（5-15s），适用于曾被风控拦截的场景 |
| `--speed-mode` | ❌ | 极速模式：去除所有延时，风控风险显著上升。与 `--safe-mode` 互斥，同时传入时 `--speed-mode` 优先 |

不传速度参数时为正常模式：内置随机延时，平衡速度与安全。**本表是速度模式语义的唯一定义**。

## 使用方式

由 `xiaohongshu-scraper` 在完成澄清阶段后自动调用。

### 固定关键词模式

```bash
python .agents/skills/xiaohongshu-fetch/scripts/fetch_xhs.py \
  --keywords "关键词1,关键词2,关键词3" \
  --max-posts 30 \
  --search-strategy '[{"keyword":"关键词1","posts_count":10,"intent":"获取整体推荐趋势"}]' \
  --output "<OUTPUT_DIR>/raw.json"
```

### 发散模式单轮

```bash
python .agents/skills/xiaohongshu-fetch/scripts/fetch_xhs.py \
  --keywords "本轮关键词" \
  --max-posts 10 \
  --output "<OUTPUT_DIR>/raw_round_1.json" \
  --seen-ids "<OUTPUT_DIR>/seen_ids.txt"
```

## 输出格式

输出的 JSON 文件包含以下字段：

| 字段 | 说明 |
|------|------|
| `search_time` | 执行时间 |
| `keywords` | 搜索关键词列表 |
| `dedup` | 抓取与去重统计：`posts_scraped`、`posts_unique`、`dropped_duplicate`、`dropped_id_mismatch` |
| `posts` | 去重后的帖子数组；每帖含 `post_id`、`url`、`card_url`、正文与互动数据，评论为 `{text, author, likes, is_reply}` 对象 |

抓取时先校验详情页实际 note id 与搜索卡片目标一致；不一致时重试一次，仍失败则丢弃并输出 `ID_MISMATCH:<expected>:<actual>`。内容按规范化后的作者、标题和正文前 300 字生成指纹，写盘前保留首次出现的记录。
