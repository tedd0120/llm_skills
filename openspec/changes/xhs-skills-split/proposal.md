## 为什么

当前 `xiaohongshu-scraper` skill 承担了过多职责：澄清、抓取、报告生成都耦合在一起。这使得代码难以维护，也无法灵活地只执行某一环节（如仅分析已有数据）。拆分后可以实现职责分离，提高代码复用性和可测试性。

## 变更内容

- **新增** `xiaohongshu-fetch` skill（内部组件，仅 scraper 调用）
  - 专注于小红书数据抓取，接收明确参数，产出 raw.json
  - 禁止用户单独调用

- **新增** `xiaohongshu-summarize` skill（对外暴露）
  - 读取 raw.json，使用 LLM 分析内容，生成 _index.md 报告
  - 用户可单独调用，用于重新分析已有数据

- **修改** `xiaohongshu-scraper` skill
  - 改为编排层角色，负责：澄清阶段、登录检查、抓取调度（发散模式下多轮循环）、结果合并、调用 summarize 和 formatter
  - 保留作为一站式入口，给用户完整体验

- **保持** `xiaohongshu-formatter` 和 `xiaohongshu-login` 不变

## 功能 (Capabilities)

### 新增功能
- `xhs-data-fetch`: 小红书数据抓取能力，支持固定关键词和发散两种模式
- `xhs-report-summarize`: 小红书数据分析报告生成能力，从 raw.json 生成结构化 _index.md

### 修改功能
- `xiaohongshu-scraper`: 从单一职责改为编排层，协调各个子 skills 完成完整流程

## 影响

- **新增目录**: `.claude/skills/xiaohongshu-fetch/`, `.claude/skills/xiaohongshu-summarize/`
- **修改文件**: `.claude/skills/xiaohongshu-scraper/SKILL.md`
- **共享脚本**: `scripts/fetch_xhs.py` 将被 fetch skill 复用
- **兼容性**: 对外 API 不变，用户调用 `/xiaohongshu-scraper` 的体验保持一致
