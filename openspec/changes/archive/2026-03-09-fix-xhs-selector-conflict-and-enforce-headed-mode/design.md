## 上下文

小红书抓取技能存在两个技术问题：

1. **命名冲突**：`scripts/selectors.py` 与 Python 标准库 `selectors` 冲突。代码中 `sys.path.insert(0, ...)` 将脚本目录置于 sys.path 最前，导致 Playwright 内部调用标准库 `selectors` 时误导入本地文件。

2. **环境检测不足**：在 WSL/无头 Linux 环境下，代码检测到无 `DISPLAY` 时静默降级到 headless 模式。这存在两个问题：
   - Agent 不知道需要启动虚拟显示器
   - headless 模式下小红书登录难以成功（风控检测）

## 目标 / 非目标

**目标：**
- 消除与 Python 标准库的命名冲突
- 强制使用有头模式，确保登录成功率
- 明确提示 WSL/无头 Linux 环境下的虚拟显示器需求
- 清理冗余代码（scraper 目录下的 fetch_xhs.py）

**非目标：**
- 不修改抓取逻辑本身
- 不添加新功能

## 决策

### 决策 1：重命名为 `xhs_selectors.py`

**选择**：将 `selectors.py` 重命名为 `xhs_selectors.py`

**理由**：
- 明确表达文件用途（小红书选择器）
- 完全避免与任何 Python 标准库冲突
- 改动最小，只需更新 import 语句

**替代方案**：
- `dom_selectors.py` — 过于通用
- `xhs_dom_selectors.py` — 更冗长，但 `xhs_selectors.py` 已足够清晰

### 决策 2：移除 headless 自动降级，强制报错退出

**选择**：在无 `DISPLAY` 时直接报错退出，输出明确的虚拟显示器启动指令

**理由**：
- Agent 需要明确知道环境需求
- headless 模式下小红书登录几乎不可能成功
- 静默降级会掩盖问题

**错误输出格式**：
```
[✗] 检测到无 DISPLAY 环境变量
    请先启动虚拟显示器:
    Xvfb :99 -screen 0 1920x1080x24 &
    export DISPLAY=:99
```

### 决策 3：合并 hyperlinks 功能到 xiaohongshu-fetch

**选择**：将 scraper 增强版 `fetch_xhs.py` 的 hyperlinks 功能合并到 xiaohongshu-fetch

**理由**：
- 符合编排设计：scraper 作为编排层调用 fetch 子 skill
- 消除代码重复
- hyperlinks 是通用功能，应在 fetch 层实现

**实现**：
- 将 `--hyperlinks` 参数和 `id_url_map.json` 生成逻辑合并到 `xiaohongshu-fetch/scripts/fetch_xhs.py`
- 删除 `xiaohongshu-scraper/scripts/fetch_xhs.py`

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 强制有头模式增加环境配置门槛 | 在 SKILL.md 中显著提示虚拟显示器配置步骤 |
| WSL 用户可能不熟悉 Xvfb | 错误消息提供完整命令示例 |
