## 新增需求

## 修改需求

### 需求: 完整流程编排
scraper 必须按以下顺序编排完整流程。

#### 场景: 一站式流程
- **当** 用户调用 `/xiaohongshu-scraper`
- **那么** scraper 必须按以下顺序执行：
  1. 澄清阶段（模式选择、关键词确认）
  2. 创建 OUTPUT_DIR
  3. 确保登录 → `xiaohongshu-login`
  4. 抓取数据 → `xiaohongshu-fetch`
  5. 合并结果（发散模式）
  6. 生成报告 → `xiaohongshu-summarize --dir $OUTPUT_DIR`
  7. 格式化 → `xiaohongshu-formatter --dir $OUTPUT_DIR`

#### 场景: 登录组件单次调用
- **当** scraper 进入执行阶段的登录步骤
- **那么** 必须只调用一次登录组件默认命令
- **并且** 由登录组件内部自行判断是否已登录或需要扫码登录
- **并且** 禁止先调用 `--check-only` 再根据结果进行第二次登录调用

## 移除需求

### 需求: 编排层预检查登录
**Reason**: 预检查模式会让编排层承担不必要的登录分支处理，并引入额外浏览器启动成本。

**Migration**: 将执行阶段的登录步骤统一替换为单次调用 `xiaohongshu-login`，成功后继续后续抓取流程。
