# xiaohongshu codex 迁移说明

## 何时使用 codex 版

优先使用 `xiaohongshu-scraper-codex` 的场景：
- 需要当前单入口 + orchestrator 执行协议
- 需要统一的 `fetch-codex + report-codex` 执行链
- 需要固定输出目录到仓库根目录 `data/xiaohongshu`
- 需要在发散模式下显式执行“篇数 + 轮数”多轮抓取

## 当前架构

- `xiaohongshu-scraper-codex`：唯一用户入口
- `xiaohongshu-fetch-codex`：内部抓取引擎
- `xiaohongshu-report-codex`：内部报告流水线
- `xiaohongshu-core-codex`：共享基础层

## 当前协议摘要

- 澄清阶段必须明确：主题、模式、帖子上限、发散轮数（仅 divergent）
- 新任务目录固定为 `data/xiaohongshu/YYYYMMDD_HHMMSS_主题`
- `fixed` 模式执行单轮抓取
- `divergent` 模式执行多轮抓取，并保留轮次元数据供报告使用
- 报告阶段保持“LLM 生成 report_draft.md，脚本 finalizer 输出 _index.md”
