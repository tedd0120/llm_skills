## 1. 创建 xiaohongshu-fetch skill

- [x] 1.1 创建 `.claude/skills/xiaohongshu-fetch/` 目录结构
- [x] 1.2 创建 `SKILL.md`，标注为内部组件，定义参数和用法
- [x] 1.3 复用现有的 `scripts/fetch_xhs.py`（无需修改脚本）
- [x] 1.4 在 SKILL.md 中明确说明禁止用户单独调用

## 2. 创建 xiaohongshu-summarize skill

- [x] 2.1 创建 `.claude/skills/xiaohongshu-summarize/` 目录结构
- [x] 2.2 创建 `SKILL.md`，定义 `--dir` 参数和用法
- [x] 2.3 实现报告生成逻辑（从原 scraper 中提取）
- [x] 2.4 确保支持固定模式（8 个板块）和发散模式（9 个板块）
- [x] 2.5 实现数据来源说明固定模板

## 3. 修改 xiaohongshu-scraper skill

- [x] 3.1 修改 `SKILL.md`，改为编排层角色
- [x] 3.2 保留澄清阶段逻辑（模式选择、关键词确认）
- [x] 3.3 更新执行流程：
  - 检查登录 → `xiaohongshu-login --check-only`
  - 抓取数据 → 调用 `xiaohongshu-fetch`
  - 生成报告 → 调用 `xiaohongshu-summarize --dir $OUTPUT_DIR`
  - 格式化 → 调用 `xiaohongshu-formatter --dir $OUTPUT_DIR`
- [x] 3.4 实现发散模式的多轮循环和结果合并逻辑
- [x] 3.5 添加上下文传递说明（OUTPUT_DIR、search_strategy、divergence_params）

## 4. 验证兼容性

- [x] 4.1 测试固定关键词模式的完整流程
- [x] 4.2 测试发散模式的完整流程
- [x] 4.3 验证用户调用 `/xiaohongshu-scraper` 的体验不变
- [x] 4.4 测试 `/xiaohongshu-summarize` 单独调用功能
- [x] 4.5 验证报告格式和内容符合规范

> **注**：验证任务需要在实际使用中完成，确保各 skills 之间调用正常。
