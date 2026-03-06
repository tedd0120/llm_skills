## 为什么

当前 `xiaohongshu-scraper` 生成的 `_index.md` 报告中，原帖引用仅为纯文本格式（如 `*《帖子标题》*`），用户无法直接点击跳转到原帖进行验证或深度阅读。当用户需要追溯来源时，必须手动复制标题去小红书搜索，体验不便。添加可选的超链接功能可以提升报告的可用性和用户体验。

## 变更内容

- **新增可选超链接功能**：在澄清阶段增加用户选择，决定报告中是否为原帖引用添加可点击超链接
- **新增 ID-URL 映射文件**：`fetch` 阶段生成 `id_url_map.json`，用于后续 URL 替换
- **修改引用格式**：`summarize` 阶段根据用户选择生成不同的 Markdown 引用格式
- **增强 formatter 功能**：新增 URL 替换逻辑，将 ID 占位符替换为实际 URL
- **保持向后兼容**：默认行为不变（超链接关闭），旧数据可正常处理

## 功能 (Capabilities)

### 新增功能

- `xhs-report-hyperlinks`: 小红书报告超链接功能。用户可选择在报告中为原帖引用添加可点击超链接，支持跳转到小红书原帖。

### 修改功能

- `xiaohongshu-browser-scraping`: 新增 `post_id` 字段提取和 `id_url_map.json` 映射文件生成
- `xiaohongshu-content-summarization`: 新增基于超链接配置的引用格式变化
- `xhs-output-enforcement`: 新增超链接格式规范和 formatter URL 替换要求

## 影响

- **修改文件**：
  - `.claude/skills/xiaohongshu-scraper/SKILL.md`：澄清阶段新增超链接选择步骤
  - `.claude/skills/xiaohongshu-scraper/scripts/fetch_xhs.py`：提取 post_id，生成 id_url_map.json
  - `.claude/skills/xiaohongshu-summarize/SKILL.md`：引用格式支持超链接占位符
  - `.claude/skills/xiaohongshu-formatter/SKILL.md`：新增 URL 替换逻辑

- **新增产出文件**（仅超链接开启时）：
  - `id_url_map.json`：帖子 ID 到完整 URL 的映射文件

- **依赖变化**：无新增外部依赖

- **向后兼容**：完全兼容，默认行为不变，旧数据正常处理
