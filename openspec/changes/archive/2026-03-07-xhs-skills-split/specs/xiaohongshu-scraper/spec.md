# 小红书爬虫执行规范（增量）

## 目的

定义 xiaohongshu-scraper skill 从单一职责改为编排层的增量规范。

---

## 修改需求

### 需求: 抓取逻辑迁移到 fetch 组件

scraper 必须不再直接包含抓取逻辑，而是调用 xiaohongshu-fetch 内部组件。

#### 场景: 固定关键词模式

- **当** 用户选择固定关键词模式（模式 A）
- **那么** scraper 必须完成澄清阶段并创建 OUTPUT_DIR
- **并且** scraper 必须调用 xiaohongshu-fetch，传入：
  - `--keywords`: 用户确认的关键词列表
  - `--max-posts`: 篇数上限
  - `--output`: `$OUTPUT_DIR/raw.json`
  - `--search-strategy`: 搜索策略 JSON
- **并且** scraper 必须等待 fetch 完成后继续

#### 场景: 发散模式

- **当** 用户选择发散模式（模式 B）
- **那么** scraper 必须完成澄清阶段并创建 OUTPUT_DIR
- **并且** scraper 必须初始化 seen_ids.txt
- **并且** scraper 必须执行循环（共 R 轮）：
  - 第 1 轮：基于用户主题生成初始关键词
  - 第 N 轮（N>1）：基于已有结果决定下一关键词
  - 每轮调用 xiaohongshu-fetch，传入：
    - `--keywords`: 本轮关键词
    - `--max-posts`: 本轮配额
    - `--output`: `$OUTPUT_DIR/raw_round_N.json`
    - `--seen-ids`: `$OUTPUT_DIR/seen_ids.txt`
  - 每轮完成后读取结果，决定下一关键词
- **并且** scraper 必须在所有轮次完成后合并 raw_round_N.json → raw.json
- **并且** scraper 必须写入 divergence_path 字段

### 需求: 报告生成迁移到 summarize 组件

scraper 必须不再直接生成报告，而是调用 xiaohongshu-summarize 组件。

#### 场景: 调用 summarize

- **当** fetch 完成并产出 raw.json
- **那么** scraper 必须调用 xiaohongshu-summarize，传入：
  - `--dir`: `$OUTPUT_DIR`
- **并且** scraper 必须等待 summarize 完成

### 需求: 完整流程编排

scraper 必须按以下顺序编排完整流程。

#### 场景: 一站式流程

- **当** 用户调用 `/xiaohongshu-scraper`
- **那么** scraper 必须按以下顺序执行：
  1. 澄清阶段（模式选择、关键词确认）
  2. 创建 OUTPUT_DIR
  3. 检查登录 → `xiaohongshu-login --check-only`
  4. 抓取数据 → `xiaohongshu-fetch`
  5. 合并结果（发散模式）
  6. 生成报告 → `xiaohongshu-summarize --dir $OUTPUT_DIR`
  7. 格式化 → `xiaohongshu-formatter --dir $OUTPUT_DIR`

### 需求: 上下文传递

scraper 必须通过目录路径在组件间传递上下文。

#### 场景: OUTPUT_DIR 共享

- **当** scraper 创建搜索目录
- **那么** 目录格式必须为 `data/xiaohongshu/YYYYMMDD_HHmmSS_主题/`
- **并且** 必须将此路径传递给 fetch、summarize、formatter
- **并且** 所有组件的输入输出文件必须在此目录下

#### 场景: 搜索策略传递

- **当** scraper 调用 fetch（固定模式）
- **那么** 必须传递 search_strategy 参数，格式为：
  ```json
  [{"keyword": "关键词一", "posts_count": 10, "intent": "搜索理由"}]
  ```

#### 场景: 发散参数传递

- **当** scraper 调用 fetch（发散模式）
- **那么** 必须传递以下参数：
  - `max_posts`: 篇数上限
  - `rounds`: 轮数
  - `round_quotas`: 各轮配额数组
  - `seen-ids`: seen_ids.txt 路径

### 需求: 保持用户调用体验

scraper 的修改必须不影响用户的调用体验。

#### 场景: 对外 API 不变

- **当** 用户调用 `/xiaohongshu-scraper`
- **那么** 用户必须能够使用相同的方式调用
- **并且** 用户必须获得相同的一站式体验
- **并且** 用户无需了解内部组件的存在

#### 场景: 澄清阶段保持

- **当** scraper 执行澄清阶段
- **那么** 必须保持原有的澄清流程（模式选择、关键词确认）
- **并且** 必须保持原有的配额分配算法
- **并且** 必须保持原有的发散模式参数确认流程
