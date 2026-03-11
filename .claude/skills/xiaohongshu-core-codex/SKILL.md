---
name: xiaohongshu-core-codex
description: 小红书 codex 共享基础层
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书共享基础层（codex）

`xiaohongshu-core-codex` 是 codex 架构的共享基础层，不作为用户入口。

它用于收敛多个组件共同依赖的基础实现：
- `xhs_selectors.py`：统一选择器定义
- `browser.py`：浏览器启动配置
- `auth.py`：认证状态路径和登录辅助
- `schema.py`：共享输入输出契约

## 约束

- codex 组件必须优先复用本层的共享脚本
- 禁止在多个 codex 技能目录中复制同类基础脚本
- 旧版重复脚本保留在旧 skills 目录中，仅供参考
