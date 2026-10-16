---
name: claude-code-usage
description: 统计本机 Claude Code 的 token 用量，展示近 7 天与近 30 天的汇总表。用户问 Claude Code 用了多少 token、用量或花费时使用。
---

# Claude Code 用量统计

运行脚本：

```bash
python <本 skill 目录>/scripts/usage.py
```

脚本通过 ccusage 读取 `~/.claude/projects` 下的会话记录，只统计 Claude Code。已归档、已删除的会话，只要记录文件还在就会计入。首次运行需要联网下载 ccusage。

最终回复原样贴出脚本输出：第一行是运行时点，其后是报告表格，表格结束即回复结束。
