---
name: xiaohongshu-scraper
description: 小红书内容抓取与分析入口。用户提到"抓小红书"、"爬小红书"、"小红书搜索"、"分析小红书内容"、"小红书帖子/评论"等场景时使用。作为编排层，协调登录、抓取（xiaohongshu-fetch）、报告生成（xiaohongshu-summarize / xiaohongshu-formatter）的完整流程。
---

# 小红书内容抓取 Skill

作为编排层，协调子组件完成从数据抓取到报告生成的完整流程。分为两个阶段：**澄清阶段**（确认参数）→ **执行阶段**（执行流水线）。

## 输出目录约定（核心要求）

所有运行产物必须写入仓库根目录下的 `data/xiaohongshu/`：

```text
OUTPUT_DIR = <仓库根目录绝对路径>/data/xiaohongshu/YYYYMMDD_HHmmSS_主题/
```

- 传给任何脚本或子组件时，OUTPUT_DIR **必须使用绝对路径**。
- 禁止在 `.agents/skills/` 下创建 data 目录或写入运行产物。
- 时间戳必须使用当前系统真实时间；报告文件固定为 `{OUTPUT_DIR}/{主题}.md`。

---

## 阶段一：澄清阶段

目标：与用户确认搜索参数。**确认前禁止进入执行阶段**。

**逐轮交互约束**：每次输出只能包含一个问题，必须等待用户回复后再输出下一个问题，禁止合并。

### 1. 解析用户意图与报告形态

从用户输入中提取核心主题，并推断 `REPORT_TYPE`（用户不反对即沿用，不再单独追问）：

| REPORT_TYPE | 判定信号 | 报告回答的核心问题 |
|:---|:---|:---|
| `recommend` | 推荐、选购、哪个好、选择、对比 | 最后选哪一个？ |
| `plan` | 攻略、行程、怎么安排、几天、执行方案 | 按什么顺序做什么？ |
| `factcheck` | 概率、是不是真的、会不会、靠谱吗、风险 | 事情到底是什么情况？ |
| `explore` | 以上都不匹配，或明确只想了解讨论全貌 | 大家在讨论什么？ |

### 2. 交互轮次流转

按顺序逐轮进行：

| 轮次 | 询问内容 | 说明与分支引导 |
|:---:|:---|:---|
| 1 | 搜索模式选择 | 展示下方模式选择表，等待回复 A / B / C |
| 2 | 篇数上限 | 询问 `篇数上限是多少？（默认 100，无上限）` |
| 3..k | 分支专属轮次 | **根据所选模式，按需查阅对应参考文件执行**：<br>• 模式 A → 阅读 [references/mode-fixed.md](references/mode-fixed.md)<br>• 模式 B → 阅读 [references/mode-divergence.md](references/mode-divergence.md)<br>• 模式 C → 阅读 [references/mode-overview-detail.md](references/mode-overview-detail.md) |
| k+1 | 速度模式 | 展示速度模式表，等待回复 S / N / Y（默认 N） |
| k+2 | 超链接格式 | 展示超链接格式表，等待回复 A / B（默认 A） |

**第 1 轮模式选择模板**：

```markdown
请先选择搜索模式：

| 选项 | 模式 | 说明 |
|:----:|:-----|:-----|
| A | 固定关键词模式 | 先确认关键词，系统按关键词执行单次搜索 |
| B | 发散模式 | 从主题出发自动多轮搜索，每轮动态决定下一关键词 |
| C | 总分模式 | 宏观关键词搜 50% 篇数，总结 top5 关键词各搜 10% 篇数 |

回复 `A`、`B` 或 `C`。
```

**速度模式与超链接选项**：
- **速度模式**：`S 安全模式`（低速抗风控）/ `N 正常模式`（默认，平衡速度安全）/ `Y 极速模式`。
- **超链接格式**：`A 纯文本`（默认，无超链）/ `B 超链接`（可点击跳转）。

**澄清阶段完成标志**：用户明确确认搜索参数（含回显的报告形态），且完成速度模式与超链接选择。完成后**立即创建 OUTPUT_DIR**，进入阶段二。

---

## 阶段二：执行阶段

进入执行阶段后，**阅读 [references/execution.md](references/execution.md)** 编排任务流水线：

1. **创建任务**：初始化 `{OUTPUT_DIR}/tasks.md` 清单。
2. **确保登录**：调用编排脚本监听扫码与状态。
3. **抓取数据**：根据模式调用 `xiaohongshu-fetch`（多轮模式按 [references/multi-round-merge.md](references/multi-round-merge.md) 合并）。
4. **生成报告**：调用 `xiaohongshu-summarize` 生成草稿。
5. **格式化报告**：调用 `xiaohongshu-formatter` 进行增强。
6. **校验与发送**：运行 `verify_tasks.py`，校验通过后发送最终报告。

*注：若遇到环境、依赖或登录异常，请查阅 [references/troubleshooting.md](references/troubleshooting.md)。*
