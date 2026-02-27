## 为什么

当前 xiaohongshu-scraper 抓取的数据包含 URL 字段，但实际使用中发现：
1. 用户很少点击报告中的原始帖子链接
2. URL 字段占用存储空间但价值有限
3. "帖子导航目录"板块使报告显得冗长

简化数据流可以减少存储、提升报告简洁性，同时不影响核心分析价值。

## 变更内容

1. **BREAKING**: 从 `fetch_xhs.py` 输出 JSON 中删除 `url` 字段
2. **BREAKING**: 从 `_index.md` 报告模板中删除"帖子导航目录"板块
3. 更新 SKILL.md 中"可追溯性"要求的描述（从"必须包含链接"改为"包含帖子标题、作者、日期"）
4. 同步更新 workflow.md 中的板块描述

## 功能 (Capabilities)

### 修改功能
- `xiaohongshu-scraper`: 抓取数据格式从 9 个字段减少到 8 个字段（删除 URL）
- `xhs-output-enforcement`: 移除"帖子导航目录"作为必需板块，调整可追溯性要求

## 影响

- **脚本代码**: `.agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py` - 删除第 248 行的 URL 字段
- **规范文档**: `.agent/skills/xiaohongshu-scraper/SKILL.md` - 更新可追溯性要求和模板
- **工作流**: `.agent/workflows/xiaohongshu-scraper.md` - 同步板块描述
- **报告模板**: `_index.md` 模板从 9 个板块减少到 8 个板块
- **已有数据**: 不影响（已有 raw.json 仍可正常读取分析）
