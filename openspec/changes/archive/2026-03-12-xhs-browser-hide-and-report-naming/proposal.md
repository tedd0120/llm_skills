# 提案：xiaohongshu技能优化 - 浏览器隐藏启动与报告命名改进

## 概述

优化小红书数据抓取技能的两个用户体验问题：
1. 浏览器窗口始终弹出在顶层，干扰用户操作
2. 报告文件命名为 `_index.md`，不够直观

## 动机

### 问题 1：浏览器窗口弹出

**当前行为**：
- 使用 `--start-minimized` 参数启动浏览器
- 该参数在 Chromium 中不可靠，窗口仍会弹出在顶层
- 每次抓取时浏览器窗口会干扰用户其他操作

**期望行为**：
- 浏览器窗口完全不可见（但不是无头模式）
- 用户可以继续其他工作，不受干扰
- 保持有头模式以避免小红书风控检测

### 问题 2：报告文件命名

**当前行为**：
- 输出目录：`data/xiaohongshu/20260312_150611_北京出发国外目的地推荐/`
- 报告文件：`_index.md`（固定名称）

**期望行为**：
- 报告文件名与搜索主题一致
- 输出示例：`北京出发国外目的地推荐.md`

## 范围

### 包含

- 修改 `login_xhs.py` 和 `fetch_xhs.py` 的浏览器启动参数
- 修改 `xiaohongshu-summarize/SKILL.md` 中的报告命名逻辑
- 修改 `xiaohongshu-formatter/SKILL.md` 中的文件读写路径
- 修改 `xiaohongshu-scraper/SKILL.md` 中的相关文档

### 不包含

- 无头模式改造（明确排除）
- 其他功能变更

## 方案

### 浏览器隐藏启动

使用 `--window-position=-2400,-2400` 参数将窗口定位到屏幕外：

```python
# 修改前
launch_kw = {"headless": False}
if sys.platform == "win32":
    launch_kw["channel"] = "msedge"
    launch_kw["args"] = ["--start-minimized"]

# 修改后
launch_kw = {"headless": False}
if sys.platform == "win32":
    launch_kw["channel"] = "msedge"
    launch_kw["args"] = ["--window-position=-2400,-2400"]
```

**优势**：
- 窗口在屏幕外，用户看不到
- 保持有头模式，渲染正常
- 小红书无法检测到窗口隐藏

### 报告命名改进

从 OUTPUT_DIR 路径解析主题名称：

```python
# 输入: "data/xiaohongshu/20260312_150611_北京出发国外目的地推荐/"
# 解析主题: "北京出发国外目的地推荐"
# 输出: "北京出发国外目的地推荐.md"

import os
dir_name = os.path.basename(output_dir.rstrip("/"))
# "20260312_150611_北京出发国外目的地推荐"
theme = dir_name.split("_", 2)[2]  # 取第三段作为主题
```

## 影响文件

| 文件 | 修改内容 |
|------|----------|
| `xiaohongshu-scraper/scripts/login_xhs.py` | 浏览器启动参数 |
| `xiaohongshu-fetch/scripts/fetch_xhs.py` | 浏览器启动参数 |
| `xiaohongshu-scraper/SKILL.md` | 文档更新 |
| `xiaohongshu-summarize/SKILL.md` | 报告命名逻辑 |
| `xiaohongshu-formatter/SKILL.md` | 文件路径逻辑 |

## 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 窗口位置参数在某些系统不生效 | 低 | 已验证 Chromium 支持此参数 |
| 主题解析失败 | 低 | 添加 fallback 到 `_index.md` |

## 成功标准

- [ ] 浏览器启动后窗口不可见
- [ ] 报告文件以主题命名
- [ ] 现有功能不受影响
