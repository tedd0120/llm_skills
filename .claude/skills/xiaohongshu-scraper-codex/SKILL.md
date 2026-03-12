---
name: xiaohongshu-scraper-codex
description: 小红书内容抓取与分析新架构入口（codex）
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书内容抓取 Skill（codex）

`xiaohongshu-scraper-codex` 是当前协议下的唯一用户入口。

它负责：
- 与用户完成澄清阶段
- 收集主题、模式、帖子上限、发散轮数等执行参数
- 调用 orchestrator 统一完成登录、抓取、报告 handoff 与 finalizer 定稿
- 将最终报告发送给用户

## 当前执行协议

### 1. 澄清顺序

开始执行前，必须按以下顺序完成澄清：

1. **主题 / 搜索意图**
2. **模式**：`fixed` / `divergent`
3. **帖子上限**：例如 `30 篇`
4. **发散轮数**：例如 `3 轮`，**仅 `divergent` 模式生效**
5. **用户确认后再执行**

可直接接受用户的自由表达，例如：
- `帮我看防晒，30篇`
- `搜索电视选购，divergent，30篇、3轮`
- `主题是宝宝餐椅，fixed，50篇`

### 2. 输出目录

新任务输出目录固定落在仓库根目录：

```text
data/xiaohongshu/YYYYMMDD_HHMMSS_主题
```

要求：
- 必须使用仓库根目录下的 `data/xiaohongshu`
- 目录名保留 `YYYYMMDD_HHMMSS_主题` 结构
- 主题文本尽量保留原始内容，只替换文件系统非法字符
- 不允许把新任务输出到仓库外部路径

### 3. 模式语义

#### `fixed`
- 按用户确认的关键词/主题执行一次抓取
- 用户自定义的帖子上限直接传给抓取层
- 不要求轮数

#### `divergent`
- 轮数是必填执行参数
- orchestrator 按轮分配总配额，并多次调用抓取引擎
- 每轮结果保存在输出目录内，最终合并为 `raw.json`
- 输出中保留轮次元数据，供报告阶段反映真实执行路径

## orchestrator 行为

### 首次执行

首次执行时，orchestrator 会：
1. 创建固定输出目录与 `tasks.md`
2. 完成登录
3. 按模式执行抓取：
   - `fixed`：单轮抓取，输出 `raw.json`
   - `divergent`：多轮抓取，输出 `raw_round_N.json`、`rounds.json`，再合并为 `raw.json`
4. 检查 `report_draft.md` 是否存在
5. 若草稿不存在，则打印明确 handoff 信息，提示先由 LLM 生成草稿
6. 若草稿已存在，则调用 report finalizer 生成 `_index.md`

### 继续报告阶段

如需在抓取完成后继续报告阶段，可复用已有目录：

```bash
python ".claude/skills/xiaohongshu-scraper-codex/scripts/orchestrator.py" --resume-dir "data/xiaohongshu/YYYYMMDD_HHMMSS_主题"
```

约束：
- `--resume-dir` 必须指向仓库根目录 `data/xiaohongshu/` 下的已有目录
- 传入仓库外路径必须拒绝

如草稿不在默认位置，可附加：

```bash
python ".claude/skills/xiaohongshu-scraper-codex/scripts/orchestrator.py" --resume-dir "data/xiaohongshu/YYYYMMDD_HHMMSS_主题" --draft "<draft_path>"
```

## 报告阶段真实边界

报告阶段内部保持以下边界不变：

1. **LLM 草稿**：读取 `raw.json`，生成完整 `report_draft.md`
2. **脚本定稿**：`build_report.py` 读取草稿并输出最终 `_index.md`

orchestrator 只负责：
- 提供目录与输入文件
- 检查草稿是否就绪
- 调用 finalizer

orchestrator 不负责用脚本替代 LLM 完成语义总结。

## 执行原则

1. 必须先完成澄清，再进入执行阶段
2. 用户确认后必须立即创建输出目录
3. 新任务必须落到仓库根目录 `data/xiaohongshu/` 下
4. `divergent` 模式必须真正按轮执行，`fixed` 模式保持单轮
5. 报告阶段必须遵循“LLM 草稿 + finalizer 定稿”的边界
