## 为什么

当前 `xiaohongshu-scraper` 的 SKILL.md 使用模糊语言（如"建议"、"推荐"），导致 Agent 可能跳过关键步骤，降低输出质量。需要引入明确的优先级约束系统，确保 Agent 严格区分核心要求、标准操作和可选路径。

## 变更内容

1. **新增三层约束标签系统**：在 SKILL.md 中引入 `[核心要求]`、`[标准操作]`、`[灵活选项]`、`[参考信息]` 四类标签
2. **重写所有模糊语言**：将"建议"、"推荐"、"可以"等词汇替换为对应优先级的明确表述
3. **新增优先级定义章节**：在 SKILL.md 开头添加 P0-P3 优先级说明和冲突处理规则
4. **同步更新工作流**：将相同的约束体系应用到 `.agent/workflows/xiaohongshu-scraper.md`

## 功能 (Capabilities)

### 新增功能
无（此变更不引入新功能，仅改进现有行为的约束表述）

### 修改功能
- `xiaohongshu-scraper`: Agent 执行规范从模糊建议改为分层强制约束

## 影响

- **文档更新**: `.agent/skills/xiaohongshu-scraper/SKILL.md` 和 `.agent/workflows/xiaohongshu-scraper.md`
- **行为变更**: Agent 将严格遵循核心要求（P0），在受阻时可降级到灵活选项（P2）
- **无代码变更**: 仅修改文档，不涉及脚本代码
