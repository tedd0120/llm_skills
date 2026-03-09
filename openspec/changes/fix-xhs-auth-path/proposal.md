# 修复小红书 Cookie 路径解析问题

## 问题

`login_xhs.py` 和 `fetch_xhs.py` 两个脚本使用相对路径读写 cookie，但由于调用时工作目录不同，导致：

- login 脚本在 `xiaohongshu-scraper` 目录下运行，cookie 被写入错误的嵌套路径
- fetch 脚本在项目根目录运行，读取的是正确路径但文件不存在

## 现象

- login 检查显示"已登录" — 它确实加载了一个有效 cookie（在错误位置）
- fetch 执行显示"未登录" — 它期望的位置没有 cookie 文件

## 解决方案

两个脚本都改用 `__file__` 计算绝对路径，确保无论工作目录如何都读写同一文件。

目标路径：
```
.claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json
```
