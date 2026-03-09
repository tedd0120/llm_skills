## 上下文

当前 Playwright 启动 Edge 浏览器时，窗口会自动获得焦点并置顶。这在 Windows 环境下会干扰用户的其他工作。

## 目标 / 非目标

**目标：**
- Windows 环境下浏览器最小化启动，不干扰用户工作
- 保持其他环境的现有行为不变

**非目标：**
- 不改变 Linux/WSL 环境的行为
- 不实现窗口位置或大小的其他配置

## 决策

### 使用 Chromium 启动参数 `--start-minimized`

**理由**：这是 Chromium 原生支持的功能，Playwright 可以通过 `args` 参数传递。

**实现方式**：
```python
launch_kw = {"headless": False}
if sys.platform == "win32":
    launch_kw["channel"] = "msedge"
    launch_kw["args"] = ["--start-minimized"]
```

**备选方案**：
- `--window-position=-2400,-2400`：将窗口移到屏幕外。缺点：窗口仍在任务栏显示，可能被用户误关闭
- Win32 API SetWindowPos：需要额外依赖，跨平台兼容性差

## 风险 / 权衡

- **[风险]** `--start-minimized` 在某些 Chromium 版本中页面加载时窗口可能自动恢复
  - **缓解措施**：这是已知行为，用户仍可手动最小化；如果问题严重，可后续改用 `--window-position` 方案
