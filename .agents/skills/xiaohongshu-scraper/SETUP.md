# 环境配置与故障排除

## Cookie 文件路径

`login_xhs.py` 与 `fetch_xhs.py` 不读取 `XHS_AUTH_STATE` 环境变量，固定使用同一份 Cookie 文件：

```text
.agents/skills/xiaohongshu-scraper/scripts/xhs_auth.json
```

实现约束：
- 路径始终基于 skill 脚本自身位置推导，不依赖当前工作目录
- `login_xhs.py` 写入后会输出 `COOKIE_FINGERPRINT[...]`，包含绝对路径、mtime、size、sha256
- `fetch_xhs.py` 读取前会输出同样口径的 `COOKIE_FINGERPRINT[...]`
- 若 login 与 fetch 的绝对路径 / 指纹不一致，应优先排查是否误用了不同文件
- 登录二维码截图固定输出到 `scripts/xhs_qr_login.png`，不会落到调用时 shell 的 cwd

## 依赖安装

```bash
pip install -r .agents/skills/xiaohongshu-scraper/scripts/requirements.txt
```

## Windows 环境

脚本会优先使用系统 Edge (`channel="msedge"`) 以减少风控特征。登录和抓取时的浏览器默认以最小化模式启动（`--start-minimized`），不会抢占前台焦点。

## Linux 无屏幕环境配置（Xvfb 虚拟显示器）⚠️ 必须

**[核心要求]** 在 Linux/WSL 服务器（无物理显示器）上运行时，必须使用 Xvfb 创建虚拟屏幕。脚本强制使用有头模式以确保登录成功率，无 `DISPLAY` 环境变量时将报错退出（headless 模式已被移除）。

```bash
# 安装 Xvfb 和依赖
sudo apt-get install -y xvfb libgbm1 libnss3 libatk-bridge2.0-0

# 启动虚拟显示器
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

## 常见限制与故障排除

| 问题 | 原因 | 处理方式 |
|-----|------|---------|
| 检测到未登录 | Cookie 过期或未登录 | 执行 `scripts/orchestrate_login.py`，由其拉起 `login_xhs.py` 并在当前会话中完成扫码登录 |
| 风控封禁 | 小红书检测到自动化 | 脚本已内置延时，**禁止取消延时** |
| 元素选择器失效 | 小红书页面改版 | 检查 `scripts/xhs_selectors.py` 并更新选择器 |
| 二维码过期或超时 | 登录等待时间过长 | 使用 `--timeout N` 调整超时时间 |
