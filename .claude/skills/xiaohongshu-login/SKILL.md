---
name: xiaohongshu-login
description: 独立处理小红书登录与 Cookie 校验，供 xiaohongshu-scraper 前置调用
license: MIT
metadata:
  author: llm-skills
  version: "1.0"
---

# 小红书登录 Skill

用于在抓取前检查小红书登录状态，必要时触发二维码登录并保存 Cookie。

## 输出状态

- `LOGIN_OK`: 当前 Cookie 有效，可直接执行抓取
- `NEED_LOGIN:<abs_path>`: 需要扫码登录，二维码路径为绝对路径
- `LOGIN_SUCCESS`: 扫码成功并已保存 Cookie
- `LOGIN_TIMEOUT`: 扫码超时
- `LOGIN_FAILED`: 登录流程异常

## 执行方式

### 1. 仅检查登录状态（推荐前置步骤）

```bash
python .claude/skills/xiaohongshu-login/scripts/login_xhs.py --check-only
```

- 返回 `LOGIN_OK`：可继续执行 scraper
- 非 `LOGIN_OK`：需要继续执行完整登录流程

### 2. 执行扫码登录

```bash
python .claude/skills/xiaohongshu-login/scripts/login_xhs.py
```

可选参数：

- `--timeout N`：扫码等待秒数，默认 `120`
- `--headless`：强制无头模式（通常不建议，用于特殊环境）

## 环境变量

```env
XHS_AUTH_STATE=.claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json
```

- 未设置时使用上述默认路径
- Cookie 将写入 `XHS_AUTH_STATE` 指定文件

## Agent 集成建议

1. 先运行 `--check-only`
2. 若非 `LOGIN_OK`，运行登录模式并根据 `NEED_LOGIN:<path>` 展示二维码给用户
3. 若得到 `LOGIN_TIMEOUT` 或 `LOGIN_FAILED`，明确告知失败并允许用户重试
4. 得到 `LOGIN_SUCCESS` 后继续调用 `xiaohongshu-scraper`
