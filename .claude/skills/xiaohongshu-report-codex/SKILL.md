---
name: xiaohongshu-report-codex
description: 小红书统一报告流水线（codex 内部组件）
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书报告组件（codex）

`xiaohongshu-report-codex` 是 codex 架构下的统一报告流水线。

它的内部协议是：**先由 LLM 生成完整语义草稿 `report_draft.md`，再由脚本 finalizer 生成最终 `_index.md`**。

## 输入与输出

### 输入
- `raw.json`：必需，LLM 读取它完成整份报告的语义归纳
- `id_url_map.json`：可选，finalizer 用于把 `(id:{post_id})` 渲染为最终帖子链接
- `report_draft.md`：必需，由 LLM 按旧版 `xiaohongshu-summarize` 模板生成的完整 Markdown 草稿

### 输出
- `_index.md`：最终可发送报告

## 职责边界

### 本组件负责
- 让 LLM 基于 `raw.json` 完成整份报告的语义分析与内容撰写
- 让 finalizer 脚本读取 `report_draft.md` 并输出 `_index.md`
- 在存在 `id_url_map.json` 时将 `(id:{post_id})` 渲染为最终链接
- 清理评论回复前缀等小红书格式残留
- 统一主标题、主要章节标题、分割线、免责声明、时间与版本字段

### 本组件不负责
- 用 Python 规则、正则、词频、情绪分析或实体识别替代 LLM 归纳
- 让脚本自动生成主题提炼、优缺点、痛点、价格、规格或情绪结论
- 把报告阶段再次拆成必须单独调用的 summarize / formatter 两个 codex 子组件

## 单组件含义

codex 的“单组件”含义是：**对编排层只暴露一个 `xiaohongshu-report-codex` skill**。

这不等于“必须把所有逻辑塞进一个 Python 脚本”。该 skill 内部允许包含：
1. LLM 归纳步骤
2. finalizer 脚本步骤

只要编排层不需要再去串联独立 summarize / formatter 组件，就符合单组件边界。

## 执行流程

### 步骤 1：读取数据
LLM 必须读取目录下的 `raw.json`，按旧版 `xiaohongshu-summarize` 的完整报告模板生成 Markdown 草稿。

### 步骤 2：生成语义草稿 `report_draft.md`
生成草稿时必须遵守以下约束：
- 所有语义总结都由 LLM 完成
- 保持旧版章节结构
- 引用帖子时继续使用旧版占位协议：`(id:{post_id})`
- 当帖子缺少 `post_id` 时，降级为纯文本引用，不生成占位符
- 数据来源说明允许先写草稿版，但最终以 finalizer 写入的固定块为准

### 步骤 3：执行 finalizer
在草稿写好后，调用：

```bash
python ".claude/skills/xiaohongshu-report-codex/scripts/build_report.py" --dir "<output_dir>"
```

如果草稿不在默认位置，可显式指定：

```bash
python ".claude/skills/xiaohongshu-report-codex/scripts/build_report.py" --dir "<output_dir>" --draft "<draft_path>"
```

### 步骤 4：产出最终报告
finalizer 会：
- 读取 `report_draft.md`
- 校验草稿至少包含“搜索概览”章节
- 用 `id_url_map.json` 将 `(id:{post_id})` 替换为最终 URL
- 清理评论中的回复前缀
- 规范主标题、主要章节标题、分割线
- 覆盖写出 `_index.md`
- 固定写入免责声明、报告生成时间和工具版本

## 草稿写作要求

生成 `report_draft.md` 时，优先遵循旧版 `xiaohongshu-summarize/SKILL.md` 的报告模板与引用格式要求。

重点保持：
- 搜索概览
- 搜索发散路径（若 `raw.json` 含 `divergence_path`）
- 品牌/主题声量分析
- 评论区高频共识
- 场景化决策建议
- 价格/规格参考
- 避雷指南
- 关键洞察
- 数据来源说明

## finalizer 的确定性职责

`build_report.py` 只保留确定性后处理职责：
- Markdown 标题和章节规范化
- `(id:{post_id})` → `https://www.xiaohongshu.com/explore/{post_id}`
- 评论清理
- 分割线补齐
- 固定免责声明块
- 时间/version 字段落盘

**禁止**在 finalizer 中新增任何语义归纳逻辑。

## 与旧版关系

- 旧版 `xiaohongshu-summarize` 仍是草稿模板的主要参考来源
- 旧版 `xiaohongshu-formatter` 仍是链接替换、评论清理、分割线和样式增强规则的参考来源
- codex 版把两者的职责收敛到同一 skill 内部，但保留“LLM 先写、脚本后处理”的真实链路
