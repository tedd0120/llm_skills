## 上下文

当前小红书爬虫 skill 的搜索流程是一次性批量执行：澄清阶段确认所有关键词后，一次调用 `fetch_xhs.py` 完成全部搜索。发散模式需要将搜索-分析-决策循环嵌入 Agent 执行流程中，实现迭代式自适应搜索。

## 目标 / 非目标

**目标：**
- 在 SKILL.md 中新增发散模式的完整执行流程
- `fetch_xhs.py` 支持跨调用去重
- 报告模板支持发散路径板块
- formatter 同步支持发散路径格式化
- 固定关键词模式完全不受影响

**非目标：**
- 不改变现有固定关键词模式的任何逻辑
- 不实现自动收敛检测（依赖固定轮数上限）
- 不实现去重后自动补量（接受实际篇数不足）

## 决策

### D1: 发散循环的执行架构

每轮发散为一次独立的 `fetch_xhs.py` 调用。Agent 在两次调用之间执行 AI 分析并决定下一个关键词。

```
Agent 循环（共 R 轮）:
  round = 1
  seen_ids_file = "{search_dir}/seen_ids.txt"
  all_posts = []
  divergence_path = []

  while round <= R:
    1. 决定本轮关键词 keyword_r
       - round=1: 基于用户主题生成初始关键词
       - round>1: AI 分析 all_posts 后决定下一个关键词，记录理由
    
    2. 调用 fetch_xhs.py:
       --keywords "{keyword_r}"
       --max-posts {per_round_quota}
       --output "{search_dir}/raw_round_{round}.json"
       --seen-ids "{seen_ids_file}"
    
    3. 读取 raw_round_{round}.json，将新帖子追加到 all_posts
    4. 记录发散路径: {round, keyword, actual_count, reason}
    5. round += 1

  合并 all_posts → raw.json（最终文件）
  生成 _index.md（含发散路径板块）
```

**理由**：多次调用比修改 fetch_xhs.py 内部循环更简单，且 Agent 本身就有 LLM 分析能力，不需要在 Python 脚本中引入 AI 调用。

### D2: 跨调用去重方案 — `--seen-ids` 参数

`fetch_xhs.py` 新增 `--seen-ids <filepath>` 参数：
- 启动时读取 file 中已有的 `note_id` 集合
- 搜索时跳过已见 note_id
- 完成后将本次新发现的 note_id 追加写入 file
- 文件格式：每行一个 note_id（纯文本）

**理由**：文件方式比内存传递更可靠（Agent 可能中断重试），且实现简单。

### D3: 发散策略 — 自由 + 轻约束

AI 的关键词决策 prompt 包含以下轻约束：
1. 下一个关键词**必须与用户原始主题保持关联**
2. 应当基于已搜索结果中发现的新方向（如高频品牌、争议点、信息盲区）
3. 应当避免与已搜索过的关键词高度重复

不预设策略矩阵，不限制发散方向类型。

### D4: 配额分配

```
每轮配额 = 篇数上限 ÷ 发散轮数（向下取整）
余数加到第一轮

示例: 50篇 ÷ 5轮 = 每轮 10 篇
示例: 50篇 ÷ 3轮 = [18, 16, 16]
```

### D5: 发散路径板块位置

在 `_index.md` 中，发散路径板块放在搜索概览之后、品牌分析之前，作为第 2 个板块（原有板块顺序往后推一位，总计 9 个板块）。

## 风险 / 权衡

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| AI 关键词漂移偏离主题 | 中 | 轻约束：必须与原始主题关联 |
| 多轮调用耗时较长 | 低 | 用户已通过设定轮数接受时间成本 |
| 去重后数据量不足 | 低 | 已确认接受，报告中标注实际篇数 |
| seen_ids 文件 I/O 增加复杂度 | 低 | 格式简单（每行一个 ID），实现直接 |
