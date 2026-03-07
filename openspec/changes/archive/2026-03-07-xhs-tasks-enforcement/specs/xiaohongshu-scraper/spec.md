## 新增需求

### 需求:SKILL.md 必须包含执行任务清单章节

xiaohongshu-scraper 的 SKILL.md 必须包含「执行任务清单」章节，定义 tasks.md 的创建和验证流程。

#### 场景:SKILL.md 包含 tasks 模板

- **当** Agent 读取 xiaohongshu-scraper SKILL.md
- **那么** 必须能找到「执行任务清单」章节
- **并且** 该章节必须包含 tasks.md 模板内容

### 需求:核心要求必须包含 tasks 验证约束

SKILL.md 的核心要求清单必须包含 tasks 创建和验证的强制约束。

#### 场景:核心要求包含 tasks 约束

- **当** Agent 读取核心要求清单
- **那么** 必须包含"进入阶段二后必须创建 tasks.md"的要求
- **并且** 必须包含"每完成一项任务必须更新 tasks.md 打勾"的要求
- **并且** 必须包含"阶段结束前必须执行 verify_tasks.py 验证"的要求

### 需求:编排层职责明确定义

xiaohongshu-scraper 作为编排层，必须明确定义其职责为：检查登录、调用 fetch 抓取数据、调用 summarize 生成报告、调用 formatter 格式化报告、发送报告。

#### 场景:编排层职责清晰

- **当** Agent 执行 xiaohongshu-scraper
- **那么** Agent 必须按顺序执行：检查登录 → 抓取数据 → 生成报告 → 格式化报告 → 发送报告
- **并且** 每个步骤完成后必须更新 tasks.md
