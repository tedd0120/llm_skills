## 1. fetch_xhs.py — 跨调用去重支持

- [x] 1.1 新增 `--seen-ids <filepath>` CLI 参数到 argparse
- [x] 1.2 启动时读取 seen-ids 文件中已有的 note_id 集合（文件不存在则创建空集合）
- [x] 1.3 修改 `_search_keyword` 方法：搜索时将文件中的 note_id 加入 `seen` 集合
- [x] 1.4 搜索完成后将本次新发现的 note_id 追加写入 seen-ids 文件（每行一个）

## 2. SKILL.md — 澄清阶段增加模式选择

- [x] 2.1 在「阶段一：澄清阶段」中，在"解析用户输入"之后、"衍生搜索关键词"之前，新增模式选择步骤
- [x] 2.2 编写模式选择展示模板（A: 固定关键词 / B: 发散模式），包含两种模式的简要说明
- [x] 2.3 编写发散模式参数收集逻辑（篇数上限、发散轮数），包含默认值和范围限制
- [x] 2.4 编写参数确认后的配额分配预览展示

## 3. SKILL.md — 执行阶段增加发散循环

- [x] 3.1 在「阶段二：执行阶段」中新增"发散模式执行步骤"章节（与现有固定模式步骤并列）
- [x] 3.2 编写发散循环逻辑：创建目录 → 轮次循环（生成关键词 → 调用 fetch_xhs.py → AI 分析 → 决策下一关键词）
- [x] 3.3 编写 AI 关键词决策的轻约束提示（必须关联原始主题、避免重复、基于结果发现新方向）
- [x] 3.4 编写数据合并逻辑：所有 raw_round_N.json 合并为 raw.json，包含 divergence_path 字段
- [x] 3.5 更新核心要求清单，新增发散模式相关的核心要求

## 4. SKILL.md — 报告模板更新

- [x] 4.1 在报告模板中搜索概览之后新增「搜索发散路径」板块模板
- [x] 4.2 更新报告板块说明表格：发散模式 9 个板块 vs 固定模式 8 个板块
- [x] 4.3 在搜索策略渲染逻辑中增加 divergence_path 字段的条件判断

## 5. xiaohongshu-formatter SKILL.md — 发散路径格式化

- [x] 5.1 在 formatter 的格式化规则中新增发散路径板块的识别和处理逻辑
- [x] 5.2 编写发散路径表格的 emoji 增强规则

## 6. OpenSpec 主规范同步

- [x] 6.1 将增量 spec 同步到主规范 `openspec/specs/xiaohongshu-search-clarification/spec.md`
- [x] 6.2 将增量 spec 同步到主规范 `openspec/specs/xiaohongshu-scraper/spec.md`
- [x] 6.3 将增量 spec 同步到主规范 `openspec/specs/xiaohongshu-scraper-report-template/spec.md`
- [x] 6.4 如果 `openspec/specs/xiaohongshu-formatter/` 不存在，创建新的主规范
