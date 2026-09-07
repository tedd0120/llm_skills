---
name: xiaohongshu-formatter
description: 小红书报告格式化组件（内部，仅 scraper 调用）。对报告草稿进行后处理：增强 emoji、替换超链接占位符、清理格式标记。
---

# 小红书报告格式化组件

> ⚠️ **内部组件** — 仅由 `xiaohongshu-scraper` 内部调用。

对传入的 `REPORT_FILE`（`{OUTPUT_DIR}/{主题}.md`）进行后处理，增强 emoji、替换超链接占位符并清理格式标记。

## 执行流程

1. **读取现有报告**：
   - 读取目标 `REPORT_FILE` 全部内容。
   - 检查 `OUTPUT_DIR` 下是否存在 `id_url_map.json`。

2. **URL 替换（超链接处理）**：
   - 若 `id_url_map.json` 存在，提取有效 `post_id` 映射；
   - 将报告中的 `(id:{post_id})` 占位符替换为可跳转 URL：`(https://www.xiaohongshu.com/explore/{post_id})`。

3. **应用格式化增强**：
   - 阅读 **[references/emoji-style.md](references/emoji-style.md)**，按规范增强标题、主要板块及关键位置的 emoji；
   - 确保主要板块之间使用 Markdown 分割线（`---`），子章节之间不加；
   - 保持原有报告事实、结构与数据不变。

4. **写回保存**：
   - 将格式化后的最终内容写回 `REPORT_FILE`。
