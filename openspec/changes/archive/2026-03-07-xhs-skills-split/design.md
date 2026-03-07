## 上下文

当前 `xiaohongshu-scraper` (v3.2) 是一个大而全的 skill，包含从澄清、抓取到报告生成的完整流程。相关组件已有：
- `xiaohongshu-login`: 独立的登录管理 skill
- `xiaohongshu-formatter`: 独立的格式化 skill

用户痛点：
- 想要只分析已有 raw.json 数据时，无法单独调用
- 想要自定义报告生成逻辑时，需要修改整个 scraper
- 发散模式的多轮循环逻辑与抓取逻辑耦合，难以测试

## 目标 / 非目标

**目标：**
- 将数据抓取和报告生成分离为独立 skills
- `xiaohongshu-fetch` 作为纯抓取工具，接收明确参数
- `xiaohongshu-summarize` 作为独立分析工具，可处理已有数据
- `xiaohongshu-scraper` 改为编排层，保持一站式体验
- 完全兼容发散搜索模式

**非目标：**
- 不修改 `xiaohongshu-formatter` 和 `xiaohongshu-login`
- 不改变用户调用 `/xiaohongshu-scraper` 的体验
- 不修改底层的 `fetch_xhs.py` 脚本实现

## 决策

### 1. 澄清阶段放在 scraper

**决策：** 澄清阶段（关键词确认、模式选择）由 scraper 负责，而非 fetch。

**理由：**
- scraper 是"智能入口"，应该处理用户交互
- fetch 设计为"纯工具"，接收明确参数执行
- 便于高级用户通过 summarize 单独分析已有数据

**替代方案考虑：** 澄清放在 fetch — 会让 fetch 更完整，但破坏了"纯工具"定位

### 2. fetch 禁止单独调用

**决策：** `xiaohongshu-fetch` 标记为内部组件，仅由 scraper 调用。

**理由：**
- fetch 需要 scraper 先完成澄清并创建目录
- 用户不应该直接操作 fetch，避免参数错误
- 将来可以随时改为对外暴露，保持扩展性

**实现方式：** 在 SKILL.md 顶部添加警告标识

### 3. 上下文通过目录路径传递

**决策：** scraper 与子 skills 之间通过 `OUTPUT_DIR` 路径共享上下文。

**理由：**
- 文件系统是最简单的共享机制
- raw.json, _index.md 都在同一目录下
- 避免复杂的进程间通信

**共享参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `OUTPUT_DIR` | string | 搜索目录路径，如 `data/xiaohongshu/20260305_120000_主题/` |
| `search_strategy` | array | 固定模式的搜索策略，传给 fetch |
| `divergence_params` | object | 发散模式的参数配置，传给 fetch |

### 4. 发散模式由 scraper 管理循环

**决策：** 发散模式的多轮循环和结果合并由 scraper 负责，fetch 只做单轮抓取。

**理由：**
- fetch 保持简单，每次"输入关键词 → 输出 raw"
- scraper 基于每轮结果决定下一关键词（AI 决策）
- 跨轮去重通过 `--seen-ids` 参数实现

**流程：**
```
Round 1: scraper → fetch → raw_round_1.json
Round 2: scraper → fetch (with --seen-ids) → raw_round_2.json
Round 3: scraper → fetch (with --seen-ids) → raw_round_3.json
scraper 合并 → raw.json
```

### 5. summarize 可独立调用

**决策：** `xiaohongshu-summarize` 对外暴露，用户可单独调用。

**理由：**
- 用户可能已有 raw.json，只想重新生成报告
- 便于调试和测试报告生成逻辑
- 与 formatter 保持一致的定位

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 目录路径传递可能出现拼写错误 | scraper 通过命令行参数 `--dir` 传递，而非手动输入 |
| fetch 被误用导致参数混乱 | 在 SKILL.md 明确标注"内部组件" |
| 发散模式结果合并逻辑复杂 | 在 scraper 中保持合并逻辑，fetch 无需关心 |
| 用户对多个 skills 感到困惑 | 保留 scraper 作为一站式入口，隐藏内部细节 |

## 架构示意

```
┌─────────────────────────────────────────────────────────────────┐
│                   对外暴露的 Skills                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /xiaohongshu-scraper     一站式入口（澄清 + 抓取 + 分析）       │
│  /xiaohongshu-summarize  分析已有 raw.json                      │
│  /xiaohongshu-formatter   格式化已有 _index.md                  │
│  /xiaohongshu-login       登录管理                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   内部 Skills（仅 scraper 调用）                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  xiaohongshu-fetch       🔒 纯抓取工具，禁止单独调用            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   scraper 内部流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 澄清阶段（固定/发散模式）                                     │
│  2. 检查登录 → xiaohongshu-login --check-only                  │
│  3. 抓取数据 → xiaohongshu-fetch                                │
│     （发散模式下多轮循环，每轮基于结果决定下一关键词）             │
│  4. 合并结果（发散模式）                                          │
│  5. 生成报告 → xiaohongshu-summarize --dir $OUTPUT_DIR          │
│  6. 格式化 → xiaohongshu-formatter --dir $OUTPUT_DIR            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 开放问题

暂无
