# 环境配置与故障排查

本文件为排障参考，仅在部署依赖或脚本运行报错时查阅。

## Cookie 与状态文件

`login_xhs.py` 与 `fetch_xhs.py` 固定使用同一份 Cookie 文件：

```text
.agents/skills/xiaohongshu-scraper/scripts/xhs_auth.json
```

- 路径由脚本根据自身位置推导，不依赖执行命令时的当前工作目录。
- 二维码截图输出到 `scripts/xhs_qr_login.png`。

## 依赖安装

```bash
pip install -r .agents/skills/xiaohongshu-scraper/scripts/requirements.txt
```

## 系统环境与适配

- **Windows**：脚本默认优先使用系统 Edge（`channel="msedge"`），启动时带 `--start-minimized`，不抢占前台焦点。
- **Linux / WSL（无物理显示器）**：必须配置 Xvfb 虚拟屏幕。脚本强制使用有头模式，缺少 `DISPLAY` 环境变量将报错退出。
  ```bash
  sudo apt-get install -y xvfb libgbm1 libnss3 libatk-bridge2.0-0
  Xvfb :99 -screen 0 1920x1080x24 &
  export DISPLAY=:99
  ```

## 常见异常排查

| 现象 | 原因 | 处理方案 |
|:---|:---|:---|
| 检测到未登录 | Cookie 过期或初次使用 | 运行 `scripts/orchestrate_login.py` 触发扫码登录 |
| 风控拦截 | 触发小红书限流 | 脚本已内置随机延时，禁止人为移除延时；可改用安全模式 |
| 选择器失效 | 小红书前端 DOM 调整 | 检查并更新 `scripts/xhs_selectors.py` |
| 二维码超时 | 等待超时 | 追加 `--timeout N` 适当调大等待时间 |
