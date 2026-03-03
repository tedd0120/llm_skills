## 为什么

当前小红书 index 报告的概览部分存在以下问题：
1. 澄清阶段的关键词分配策略（篇数+搜索意图）在执行后丢失
2. 「字段」「值」表头描述生硬，用户体验不佳
3. Emoji 使用不足，报告可读性有待提升

这是在首次使用抓取技能后发现的改进机会。

## 变更内容

- **新增** `search_strategy` 字段到 `raw.json` 顶层，保存关键词、篇数、搜索意图的映射
- **修改** `fetch_xhs.py` 脚本，接收并保存 `search_strategy` 元数据
- **修改** 报告概览模板，采用嵌入式设计（方案A）
- **移除** Markdown 表头中的 `<b>` 冗余标签（表头自动加粗）
- **改进** 表头列名，替换「字段」「值」为更友好的描述
- **增加** Emoji 使用，提升报告可读性

## 功能 (Capabilities)

### 新增功能
- `xhs-search-strategy-persistence`: 搜索策略元数据持久化功能，保存关键词分配策略到 raw.json

### 修改功能
- `xiaohongshu-scraper-report-template`: 报告模板格式改进，概览部分采用新的嵌入式设计

## 影响

- **代码**: `.claude/skills/xiaohongshu-scraper/scripts/fetch_xhs.py`
- **文档**: `.claude/skills/xiaohongshu-scraper/SKILL.md` 中的报告模板
- **数据格式**: `raw.json` 新增 `search_strategy` 字段（向后兼容）
