## 为什么

其他 Agent 在调用 xiaohongshu-scraper 时报告了两个问题：

1. **命名冲突**：`scripts/selectors.py` 与 Python 标准库 `selectors` 模块同名，导致 Playwright 启动时误导入本地文件而非标准库，抛出 `AttributeError`。

2. **WSL 环境问题**：在 WSL/无头 Linux 环境下，代码会静默降级到 headless 模式，而不是明确提示需要启动虚拟显示器。这导致 Agent 不清楚环境需求，且 headless 模式下小红书登录难以成功。

## 变更内容

1. **重命名 `selectors.py` → `xhs_selectors.py`**：避免与 Python 标准库命名冲突
2. **强制有头模式**：移除自动降级到 headless 的逻辑，在无 `DISPLAY` 环境变量时报错退出并提示启动虚拟显示器
3. **合并 hyperlinks 功能到 fetch**：将 xiaohongshu-scraper 目录下的增强版 `fetch_xhs.py` 的 hyperlinks 逻辑合并到 xiaohongshu-fetch
4. **删除冗余文件**：移除 xiaohongshu-scraper 目录下的 `fetch_xhs.py`（scraper 作为编排层应调用 fetch 子 skill）
5. **更新 SKILL.md**：在显著位置强制提示有头模式的环境需求

## 功能 (Capabilities)

### 新增功能

无

### 修改功能

- `xiaohongshu-scraper`: 强制有头模式环境要求，删除冗余的 fetch_xhs.py
- `xhs-data-fetch`: 重命名 selectors.py，强制有头模式，合并 hyperlinks 功能

## 影响

**受影响的文件**：
- `.claude/skills/xiaohongshu-scraper/scripts/selectors.py` → 重命名为 `xhs_selectors.py`
- `.claude/skills/xiaohongshu-scraper/scripts/fetch_xhs.py` → 删除
- `.claude/skills/xiaohongshu-scraper/scripts/login_xhs.py` → 移除 headless 自动降级逻辑
- `.claude/skills/xiaohongshu-scraper/SKILL.md` → 强制提示有头模式环境需求
- `.claude/skills/xiaohongshu-fetch/scripts/selectors.py` → 重命名为 `xhs_selectors.py`
- `.claude/skills/xiaohongshu-fetch/scripts/fetch_xhs.py` → 移除 headless 自动降级逻辑，合并 hyperlinks 功能

**受影响的 Agent**：所有在 WSL/无头 Linux 环境下调用小红书抓取功能的 Agent
