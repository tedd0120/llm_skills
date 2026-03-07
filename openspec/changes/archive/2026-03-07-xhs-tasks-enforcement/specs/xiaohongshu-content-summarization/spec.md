## 移除需求

### 需求:生成报告后必须继续执行格式化步骤

**Reason**: 格式化职责已迁移到 xiaohongshu-scraper 编排层，summarize 只负责生成 `_index.md`。

**Migration**: 由 xiaohongshu-scraper 在调用 summarize 后，自行调用 xiaohongshu-formatter。

#### 场景:旧行为（已移除）

- ~~当~~ summarize 生成 `_index.md`
- ~~那么~~ 必须继续阅读 formatter/SKILL.md 并执行格式化
- ~~并且~~ 必须发送报告到用户对话框

### 需求:生成报告后必须发送到用户对话框

**Reason**: 发送职责已迁移到 xiaohongshu-scraper 编排层。

**Migration**: 由 xiaohongshu-scraper 在格式化完成后，负责发送最终报告。

#### 场景:旧行为（已移除）

- ~~当~~ summarize 完成报告生成和格式化
- ~~那么~~ 必须将报告发送到用户对话框

## 新增需求

### 需求:summarize 只负责生成 _index.md

xiaohongshu-summarize 的职责边界明确为：读取 raw.json，生成 `_index.md`，结束。

#### 场景:生成报告后结束

- **当** summarize 成功生成 `_index.md`
- **那么** 任务完成
- **禁止** 自动执行格式化或发送操作
