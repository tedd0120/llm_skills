# xiaohongshu codex 迁移说明

## 何时使用 codex 版

优先使用 `xiaohongshu-scraper-codex` 的场景：
- 需要采用新的单入口 + orchestrator 架构
- 需要统一的 `fetch-codex + report-codex` 执行链
- 需要减少旧版文档漂移带来的歧义

## 何时参考旧版

继续参考旧版小红书 skills 的场景：
- 需要核对历史行为或已有调用约定
- 需要对比旧版 `summarize + formatter` 的拆分链路
- 需要确认旧目录中的脚本实现细节

## 架构差异

- codex 版只推荐 `xiaohongshu-scraper-codex` 作为用户入口
- 登录不再作为 codex 体系中的独立 skill，而是 orchestrator 内部认证步骤
- 报告阶段由 `xiaohongshu-report-codex` 单组件完成
- 共享基础脚本统一收敛到 `xiaohongshu-core-codex`

## 兼容策略

- 原有 `xiaohongshu-scraper`、`xiaohongshu-fetch`、`xiaohongshu-summarize`、`xiaohongshu-formatter` 保持不变
- codex 版新增目录不会覆盖旧实现
