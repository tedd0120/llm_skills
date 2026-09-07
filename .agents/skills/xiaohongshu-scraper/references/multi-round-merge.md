# 多轮模式数据合并规则（发散 / 总分）

本文件供发散模式（模式 B）与总分模式（模式 C）在抓取完成后合并多轮原始数据为 `raw.json` 时查阅。

## 合并规则

1. **拼接与去重**：
   - 按轮次顺序拼接所有轮次的 `posts` 数组。
   - 使用内容指纹（规范化作者 + 标题 + 正文前 300 字哈希）去重，保留首次出现的记录；禁止使用 LLM 判断重复。

2. **统计字段汇总**：
   - `dedup.posts_scraped`：各轮原始抓取数累加之和。
   - `dedup.posts_unique`：最终去重后的帖子数。
   - `dedup.dropped_duplicate`：`posts_scraped - posts_unique`。
   - `dedup.dropped_id_mismatch`：各轮之和。

3. **路径元数据注入**：
   合并后的 `raw.json` 必须追加搜索路径字段，以便报告组件还原搜索过程：
   - **发散模式**：写入 `divergence_path` 数组。
   - **总分模式**：写入 `overview_detail_path` 数组。
   - 每个元素包含：`round`（轮次序号）、`keyword`（该轮关键词）、`actual_posts`（实际抓取篇数）、`note`（发散理由 / 宏观说明或 top5 入选理由）。
