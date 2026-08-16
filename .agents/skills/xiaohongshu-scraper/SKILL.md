---
name: xiaohongshu-scraper
description: 小红书内容抓取与分析入口。用户提到"抓小红书"、"爬小红书"、"小红书搜索"、"分析小红书内容"、"小红书帖子/评论"等场景时使用。作为编排层，协调登录、抓取（xiaohongshu-fetch）、报告生成（xiaohongshu-summarize / xiaohongshu-formatter）的完整流程。
---

# 小红书内容抓取 Skill

作为编排层，协调子 skills 完成从数据抓取到报告生成的完整流程。流程分两阶段：**澄清阶段**（与用户确认参数）→ **执行阶段**（编排抓取与报告生成）。

**内部架构**：
- `scripts/orchestrate_login.py` - 登录编排入口，轮询 `login_xhs.py` 输出并收敛为稳定事件
- `xiaohongshu-fetch` - 浏览器自动化抓取，输出 raw.json（参数与速度模式语义见其 SKILL.md）
- `xiaohongshu-summarize` - 分析 raw.json 生成结构化报告
- `xiaohongshu-formatter` - 美化报告格式、替换超链接占位符

**披露文件**（按需阅读）：
- [modes.md](modes.md) - 模式 A / 模式 B 的分支专属交互轮次、发散模式执行约束与决策报告格式
- [SETUP.md](SETUP.md) - 依赖安装、Cookie 文件、Linux/Xvfb 配置、故障排除

## 输出目录约定（核心要求）

**所有运行产物必须写入仓库根目录下的 `data/xiaohongshu/`**：

```
OUTPUT_DIR = <仓库根目录绝对路径>/data/xiaohongshu/YYYYMMDD_HHmmSS_主题/
```

- 传给任何脚本或子 skill 时，OUTPUT_DIR **必须使用绝对路径**（脚本按 cwd 解析相对路径，容易走错）
- **禁止**在 `.agents/skills/` 任何 skill 目录下创建 data 目录或写入运行产物
- 时间戳必须使用当前系统时间，禁止使用示例、模板或虚构时间
- 主题名由你根据用户输入的主旨概括；报告文件为 `{OUTPUT_DIR}/{主题}.md`

---

## 阶段一：澄清阶段（必须执行）

目标：与用户确认搜索参数。**确认前禁止进入执行阶段**。

**逐轮交互约束（核心要求）**：每次输出只能包含一个问题，必须等待用户回复后再输出下一个问题，禁止合并多个问题到一次输出。

### 1. 解析用户输入

- 将用户输入视为整体文本，忽略内部所有分隔符（逗号、空格、分号等）
- 理解主旨，识别核心要素：主题、地域、场景、意图
- 示例：输入 "广州装修公司, 对比, 避坑" 应理解为 "广州装修公司相关" 这一整体建议
- 同时推断 `REPORT_TYPE`，不要增加强制问答轮：

  | REPORT_TYPE | 判定信号 | 报告回答 |
  |:--|:--|:--|
  | `recommend` | 推荐、选购、哪个好、选择、对比，或明显期待一个可行动的候选结论 | 最后选哪一个？ |
  | `plan` | 攻略、行程、怎么安排、几天、执行方案 | 按什么顺序做什么？ |
  | `factcheck` | 概率、是不是真的、会不会、靠谱吗、风险 | 事情到底是什么情况？ |
  | `explore` | 以上都不匹配，或用户明确只想了解讨论/争议全貌 | 大家在讨论什么？ |

- 在模式 A 的关键词确认或模式 B 的配额确认中回显 `报告形态：<中文名>（REPORT_TYPE）`；用户一句话即可覆盖。用户不反对即沿用推断值，不再单独追问。

### 2. 交互轮次

按顺序逐轮进行：

| 轮次 | 内容 | 说明 |
|:----:|:-----|:-----|
| 1 | 搜索模式选择 | 展示下方模式表，等待回复 A/B |
| 2 | 篇数上限 | `篇数上限是多少？（默认 100，无上限）` |
| 3..k | 分支专属轮次 | **按所选模式阅读 [modes.md](modes.md) 执行**：模式 A 为关键词衍生与确认；模式 B 为发散轮数与配额确认 |
| k+1 | 速度模式 | 展示下方速度模式表，等待回复 S/N/Y |
| k+2 | 超链接格式 | 展示下方超链接格式表，等待回复 A/B |

**第 1 轮模式选择模板**：

```markdown
请先选择搜索模式：

| 选项 | 模式 | 说明 |
|:----:|:-----|:-----|
| A | 固定关键词模式 | 你先确认关键词，系统按关键词一次性执行搜索 |
| B | 发散模式 | AI 从主题出发自动多轮搜索，每轮动态决定下一关键词 |

回复 `A` 或 `B`。
```

**速度模式轮模板**：

```markdown
选择速度模式：

| 选项 | 模式 | 说明 |
|:----:|:-----|:-----|
| S | 安全模式 | 延迟增大 + 随机阅读停顿，最大限度规避风控 |
| N | 正常模式（默认） | 内置随机延时，平衡速度与安全 |
| Y | 极速模式 | 保留轻微随机延时，快速抓取但仍可能触发风控 |

回复 `S`、`N` 或 `Y`（默认 N）。
```

**超链接格式轮模板**：

```markdown
报告中超链接格式：

| 选项 | 格式   | 说明                              |
|:----:|:------|:----------------------------------|
| A    | 纯文本  | 原帖引用为纯文本，无超链接（默认）     |
| B    | 超链接  | 原帖引用可直接点击跳转到小红书       |

回复 `A` 或 `B`（默认 A）。
```

**澄清阶段完成标志**：用户明确确认关键词（模式 A）或发散参数（模式 B，确认内容含报告形态），且完成速度模式与超链接格式选择。完成后**立即**按上方目录约定创建 OUTPUT_DIR，再进入阶段二。

---

## 阶段二：执行阶段

**编排层职责**：确保登录 → 抓取数据 → 生成报告 → 格式化报告 → 发送报告。

### 执行任务清单

进入阶段二后，立即将以下内容写入 `{OUTPUT_DIR}/tasks.md`：

```markdown
## 执行任务清单

- [ ] 确保登录
- [ ] 抓取数据
- [ ] 生成报告
- [ ] 格式化报告
- [ ] 发送报告
```

**核心要求**：
- 每完成一项任务，立即将对应 `[ ]` 改为 `[x]`
- 阶段二结束前，必须按步骤 5 的完整命令验证任务、raw.json 与报告；任何 `RUN_INVALID` 必须报错中止，禁止发送未通过验证的报告

### 步骤 1：确保登录

```text
1) 读取 LOGIN_POLL_INTERVAL_SEC（默认 2，建议 1-10；非法值脚本自动回退到 2）
2) 调用：python .agents/skills/xiaohongshu-scraper/scripts/orchestrate_login.py --poll-interval <LOGIN_POLL_INTERVAL_SEC> --output-dir <OUTPUT_DIR 绝对路径>
   - orchestrate_login.py 会自动创建目录和 tasks.md（如不存在）
   - 可选追加 `--timeout <秒>` 调整扫码等待超时（默认 120 秒）
3) 监听输出：原样透传 login_xhs.py 输出（保留 COOKIE_FINGERPRINT 等排障信息），重点关注 LOGIN_EVENT: {...} 结构化事件
4) 出现 NEED_LOGIN:<abs_path> 或对应 LOGIN_EVENT：立即向用户发送
   "请扫码登录小红书。二维码文件：<abs_path>"
5) 出现 LOGIN_OK / LOGIN_SUCCESS（或对应 LOGIN_EVENT）：orchestrate_login.py 会将 tasks.md 中"确保登录"标记完成，继续下一步
6) 出现 LOGIN_TIMEOUT / LOGIN_FAILED / ORCHESTRATOR_ERROR：报错并中止执行阶段
```

### 步骤 2：抓取数据 → xiaohongshu-fetch

- 固定模式：单次调用 fetch → `raw.json`
- 发散模式：多轮循环调用 fetch（每轮约束与决策报告见 [modes.md](modes.md)）→ 合并为 `raw.json`
- 启用超链接时 fetch 生成 `id_url_map.json`

### 步骤 3：生成报告 → xiaohongshu-summarize

阅读其 SKILL.md，将 `REPORT_TYPE` 与 raw.json 一并交给组件，生成 `{OUTPUT_DIR}/{主题}.md`。

### 步骤 4：格式化报告 → xiaohongshu-formatter

阅读其 SKILL.md，对 `{OUTPUT_DIR}/{主题}.md` 增强 emoji、替换超链接占位符、清理格式标记。

### 步骤 5：发送报告

先执行下列产物验证；仅通过后才将最终报告发送到用户对话框：

```text
python .agents/skills/xiaohongshu-scraper/scripts/verify_tasks.py <tasks_file_path> --report-file <REPORT_FILE> --report-type <REPORT_TYPE>
```

启用超链接时追加 `--hyperlinks`。验证失败必须中止发送并修复产物。

### 上下文传递

| 参数 | 类型 | 说明 | 传递给 |
|------|------|------|--------|
| `OUTPUT_DIR` | string | 搜索目录**绝对路径**（见目录约定） | fetch, summarize, formatter |
| `REPORT_FILE` | string | 报告文件路径 `{OUTPUT_DIR}/{主题}.md`，由 scraper 确定 | summarize, formatter |
| `REPORT_TYPE` | enum | `recommend` / `plan` / `factcheck` / `explore`；由 scraper 推断、用户可覆盖 | summarize, verify_tasks |
| `--keywords` / `--max-posts` | flag | 搜索关键词与篇数上限 | fetch |
| `--search-strategy` | flag (JSON) | 固定模式搜索策略 | fetch |
| `--seen-ids` | flag (path) | 发散模式跨轮去重 ID 文件 | fetch |
| `--hyperlinks` | flag | 启用超链接（fetch 生成 `id_url_map.json`，summarize 产出 `id:{post_id}` 占位符，formatter 替换为 URL） | fetch, summarize, formatter |
| `--speed-mode` / `--safe-mode` | flag | 极速 / 安全模式，语义与优先级以 fetch 的 SKILL.md 为准。用户选择极速模式时，风控风险由其自行承担 | fetch |
