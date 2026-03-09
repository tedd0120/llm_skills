## 为什么

当前在 Windows 环境下启动 Edge 浏览器进行小红书抓取时，浏览器窗口会自动置顶并获得焦点，干扰用户的其他工作。

## 变更内容

- 在 Windows 环境下启动 Edge 浏览器时，添加 `--start-minimized` 参数使窗口最小化启动
- 不影响其他环境（Linux/WSL）的现有行为

## 功能 (Capabilities)

### 新增功能

无

### 修改功能

- `xhs-data-fetch`: 浏览器启动行为变更 - Windows 下最小化启动
- `xhs-login`: 浏览器启动行为变更 - Windows 下最小化启动

## 影响

- `xiaohongshu-fetch/scripts/fetch_xhs.py` - 修改浏览器启动参数
- `xiaohongshu-scraper/scripts/login_xhs.py` - 修改浏览器启动参数
