## 为什么

当前小红书技能在生成 `_index.md` 报告时，某些 AI 会调用 Python 脚本（如 `re` 正则匹配、`collections.Counter` 词频统计）进行结构化分析。这种自动化脚本无法理解语义上下文，导致报告机械、可读性差（例如将"好坑"识别为"好"的优点）。需要约束 Agent 使用 LLM 的自然语言理解能力进行内容分析。

## 变更内容

- **新增 [核心要求]**：禁止调用外部脚本进行文本分析或内容提取（包括 Python re 正则、collections.Counter 词频统计、实体识别、情感分析脚本等）
- **明确边界**：允许基本数值统计（如帖子数量、评论总数），但内容理解、分析、总结必须基于 LLM 自然语言理解
- **移除 Python 代码示例**：删除 SKILL.md 中可能诱导 Agent 使用脚本的内容（如 `sum(post["comments_count"]...)` 代码片段、`map_intent_emoji()` 函数）
- **Emoji 自由化**：移除固定 emoji 映射表格，让 Agent 根据上下文自行判断使用何种 emoji 及位置
- **调整计数格式**：将"提及 ~X 次"改为定性描述（如"多位用户提到"、"广泛讨论"）

## 功能 (Capabilities)

### 新增功能
- `xhs-ai-only-analysis`: 小红书报告生成必须使用 AI 自然语言理解，禁止自动化语义分析脚本

### 修改功能
- `xiaohongshu-scraper`: 小红书抓取技能的行为约束更新

## 影响

- **受影响文件**：`.claude/skills/xiaohongshu-scraper/SKILL.md`
- **行为变更**：Agent 生成 `_index.md` 时不再调用语义分析脚本，报告质量提升，可读性增强
- **向后兼容**：不破坏现有功能，仅添加约束
