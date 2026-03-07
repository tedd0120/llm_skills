## 为什么

Agent 在执行 xiaohongshu-scraper 时经常遗漏步骤（如检查登录、格式化报告、发送报告）。当前的「核心要求」是静态文档，缺少运行时的强制检查机制。

引入运行时 tasks.md 机制：在执行阶段开始时创建任务清单，每完成一步必须打勾，阶段结束前验证全部完成。

## 变更内容

- **新增** tasks 模板章节到 xiaohongshu-scraper SKILL.md
- **新增** `scripts/verify_tasks.py` 验证脚本
- **修改** xiaohongshu-summarize SKILL.md，删除格式化和发送职责（由 scraper 编排层负责）
- **修改** xiaohongshu-scraper SKILL.md 核心要求，增加 tasks 创建和验证的强制约束

## 功能 (Capabilities)

### 新增功能

- `xhs-tasks-enforcement`: 运行时任务清单机制，包含 tasks.md 创建、打勾更新、阶段结束验证

### 修改功能

- `xiaohongshu-scraper`: 增加 tasks 模板章节和验证要求；明确编排层职责（检查登录、抓取、生成报告、格式化、发送）
- `xiaohongshu-content-summarization`: 删除输出要求中的格式化和发送职责，明确只负责生成 `_index.md`

## 影响

- `xiaohongshu-scraper/SKILL.md` - 新增 tasks 章节
- `xiaohongshu-summarize/SKILL.md` - 删除格式化和发送职责
- `scripts/verify_tasks.py` - 新增验证脚本
