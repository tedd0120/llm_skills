## 1. 建立 codex 技能骨架

- [x] 1.1 创建 `xiaohongshu-scraper-codex`、`xiaohongshu-fetch-codex`、`xiaohongshu-report-codex` 和 `xiaohongshu-core-codex` 目录结构
- [x] 1.2 为各 codex 技能编写基础 `SKILL.md`，明确入口边界、内部组件边界和新旧并存关系
- [x] 1.3 在 `scraper-codex` 中建立 orchestrator 脚本入口，并保留阶段化进度与任务校验结构

## 2. 抽取共享基础层

- [x] 2.1 将重复的选择器、浏览器配置、认证状态解析与共享 schema 收敛到 `xiaohongshu-core-codex`
- [x] 2.2 更新 `fetch-codex` 和 `scraper-codex` 对共享基础脚本的引用，避免重复实现

## 3. 重组抓取与报告流水线

- [x] 3.1 迁移现有抓取逻辑到 `xiaohongshu-fetch-codex`，保留固定模式、发散模式单轮抓取与去重能力
- [x] 3.2 合并 summarize 与 formatter 的职责到 `xiaohongshu-report-codex`，统一生成最终 `_index.md`
- [x] 3.3 调整 orchestrator 使其只调用 `fetch-codex` 与 `report-codex` 完成完整执行链

## 4. 清理冗余脚本与文档描述

- [x] 4.1 清理 codex 文档中失效的独立 login skill 引用，统一改为内部认证步骤说明
- [x] 4.2 清理 codex 版重复的报告模板、重复职责说明和重复基础脚本布局
- [x] 4.3 更新 README 中的小红书模块说明，标记 codex 为推荐入口并说明旧版保留

## 5. 验证与迁移说明

- [x] 5.1 检查所有新产物路径、技能说明与 OpenSpec 产出物保持一致
- [x] 5.2 编写最小迁移说明，说明何时使用 codex 版、何时参考旧版
- [x] 5.3 运行必要的结构与文档自检，确认 apply 前提已满足