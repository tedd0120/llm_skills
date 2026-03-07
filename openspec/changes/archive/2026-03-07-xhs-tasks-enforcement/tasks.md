## 1. 创建验证脚本

- [x] 1.1 创建 `scripts/verify_tasks.py` 脚本
- [x] 1.2 实现读取 tasks.md 并统计 `[ ]` 和 `[x]` 数量的逻辑
- [x] 1.3 输出格式：`TASKS_COMPLETE: N/N` 或 `TASKS_INCOMPLETE: N/N` + 未完成项列表
- [x] 1.4 返回退出码：全部完成返回 0，有未完成项返回 1

## 2. 修改 xiaohongshu-scraper SKILL.md

- [x] 2.1 新增「执行任务清单」章节，包含 tasks.md 模板
- [x] 2.2 在核心要求中添加 tasks 创建和验证的强制约束
- [x] 2.3 更新执行流程图，增加创建 tasks.md 和验证步骤
- [x] 2.4 明确编排层职责边界（检查登录 → 抓取 → 生成报告 → 格式化 → 发送）

## 3. 修改 xiaohongshu-summarize SKILL.md

- [x] 3.1 删除"输出要求"中关于格式化和发送的职责
- [x] 3.2 明确 summarize 只负责生成 `_index.md`
- [x] 3.3 删除"必须继续执行格式化步骤"的核心要求
- [x] 3.4 删除"必须将报告发送到用户对话框"的核心要求

## 4. 验证

- [x] 4.1 测试 verify_tasks.py 脚本对全部完成和部分完成场景的处理
- [x] 4.2 验证修改后的 SKILL.md 结构完整
- [x] 4.3 确认职责边界清晰，无遗漏或重复
