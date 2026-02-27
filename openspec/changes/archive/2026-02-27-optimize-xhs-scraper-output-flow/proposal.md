## 为什么

当前 xiaohongshu-scraper 的工作流程需要为每个抓取的帖子生成独立的 Markdown 文件（20 篇帖子 = 20 个文件），但实际使用中用户基本不查看这些单篇文件，主要价值在于最终的汇总报告。这导致：
- **资源浪费**：生成大量低价值文件（token 消耗、时间成本）
- **流程冗余**：AI 需要先写单篇 MD，再读取它们生成汇总报告
- **用户负担**：20+ 个文件让用户难以找到有价值的信息

简化流程，专注于生成高质量的增强版汇总报告是更优方案。

## 变更内容

### 新功能
无新增功能

### 修改功能
- **删除单篇 MD 生成环节**：移除"数据总结写入（生成子 Markdown）"步骤（原 Step 4）
- **增强汇总报告模板**：将 _index.md 从基础导航升级为深度分析报告，包含：
  - 品牌/主题声量分析
  - 多维对比矩阵
  - 评论区高频共识统计（优点 Top 5 / 痛点 Top 5）
  - 场景化决策建议（决策树）
  - 价格/规格参考（从评论中提取）
  - 避雷指南
  - 关键洞察

**BREAKING**: 不再生成单篇帖子 MD 文件，输出目录中只有 `_index.md`（可选择保留原始 JSON）

### 工作流程简化
- **原流程**：JSON → 20 个单篇 MD → 读取所有 MD → 生成 index
- **新流程**：JSON → 直接读取 → 生成增强版 index

## 功能 (Capabilities)

### 新增功能
无

### 修改功能
- `xiaohongshu-content-summarization`: 修改内容汇总流程，从"多文件生成+汇总"简化为"直接生成汇总报告"

## 影响

- **受影响的文件**：
  - `.agent/skills/xiaohongshu-scraper/SKILL.md` - 主要修改对象
    - 删除第 116-142 行（单篇 MD 生成步骤）
    - 修改第 77-81 行（强制输出规范）
    - 替换第 144-190 行（_index.md 模板）
  - `.agent/workflows/xiaohongshu-scraper.md` - 同步更新工作流描述

- **不影响的文件**：
  - `.agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py` - 爬虫脚本无需修改
  - `.agent/skills/xiaohongshu-scraper/scripts/selectors.py` - 选择器无需修改

- **用户影响**：
  - ✅ 用户体验提升：直接获得高质量分析报告
  - ✅ 执行速度提升：减少文件 I/O 和 token 消耗
  - ⚠️ 失去单篇存档：如需单个帖子详情，需跳转到原小红书链接
