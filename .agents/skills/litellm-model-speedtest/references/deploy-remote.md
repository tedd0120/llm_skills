# HTML 报告远程部署（SCP）

本文件供配置或执行将测速 HTML 报告同步部署至远程 Web 服务器时查阅。

## 环境配置

在仓库根目录 `.env` 中配置部署参数：

```bash
# 目标服务器及部署绝对路径（必填）
SPEEDTEST_DEPLOY_TARGET=aliyun:/var/www/speedtest/index.html

# SSH 端口（可选，默认 22）
SPEEDTEST_DEPLOY_PORT=2222

# 私钥路径（可选，默认使用系统 SSH 密钥）
# SPEEDTEST_DEPLOY_KEY=~/.ssh/id_rsa

# 公网访问 URL（配置后自动打印并由浏览器打开）
# SPEEDTEST_DEPLOY_URL=https://speedtest.yourdomain.com
```

## 执行方式

- **自动推送**：配置上述环境变量后，脚本生成 HTML 时会自动触发 SCP 推送并在终端打印公网链接。
- **仅推送已有报告**（无需重新测速）：
  ```bash
  python "<skill-dir>/scripts/speedtest.py" --deploy-only
  ```
- **临时跳过推送**：
  ```bash
  python "<skill-dir>/scripts/speedtest.py" --no-deploy
  ```
