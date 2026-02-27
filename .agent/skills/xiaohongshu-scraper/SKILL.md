---
description: 抓取小红书帖子和评论并在 Agent 场景中进行 AI 总结
---

# 小红书内容抓取 Skill

通过自动化浏览器（Playwright）抓取小红书上的帖子正文和评论区内容。作为 Agent，你需要调用此 Skill 提供的脚本获取原始数据，然后将数据进行 AI 总结并整理输出。

## 🎯 前置依赖配置

请确保用户在 `.env` 中添加了此配置，用于保存登录的持久化 state（Cookie 等）：
```env
XHS_AUTH_STATE=.agent/skills/xiaohongshu-scraper/scripts/xhs_auth.json
```

需要安装脚本依赖：
```bash
pip install -r .agent/skills/xiaohongshu-scraper/scripts/requirements.txt
```

对于 Windows 有头模式，脚本会优先使用系统 Edge (`channel="msedge"`) 以减少风控特征。

### Linux 无屏幕环境配置（Xvfb 虚拟显示器）

在 Linux 服务器（无物理显示器）上运行时，推荐使用 Xvfb 创建虚拟屏幕以启动**有头模式浏览器**，这比 headless 模式更不容易被小红书检测：

```bash
# 1. 安装 Xvfb 和 Chromium 依赖
sudo apt-get update
sudo apt-get install -y xvfb libgbm1 libnss3 libatk-bridge2.0-0 libxkbcommon0 \
    libgtk-3-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libasound2

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 启动虚拟显示器 (1920x1080 分辨率, 24位色深)
Xvfb :99 -screen 0 1920x1080x24 &

# 4. 设置 DISPLAY 环境变量
export DISPLAY=:99

# 5. 正常运行脚本 (不加 --headless，将以有头模式在虚拟屏幕中运行)
python .agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py --keywords "搜索词"
```

> **提示**: 可将 `export DISPLAY=:99` 写入 `.bashrc` 或 `.env` 中持久化。如果使用 systemd 管理 agent 服务，在 service 文件的 `[Service]` 段添加 `Environment=DISPLAY=:99`。

如果不想安装 Xvfb，也可以直接使用 `--headless` 参数降级为无头模式，但被风控检测的概率更高。

---

## 🛠️ CLI 基础用法

代理脚本采用命令行调用。你可以通过写入临时文件或直接捕获 stdout 获得 JSON 输出。

```bash
# 基础搜索 (默认上限 20 篇结果)
python .agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py --keywords "2026年春季穿搭"

# 多词联合搜索并指定输出文件, 指定上限 50 篇（硬上限 100）
python .agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py --keywords "春装搭配,早春outfit" --max-posts 50 --output "data/tmp_xhs_raw.json"

# 强制开启无头模式 (通常在 Linux 环境下或不需要看到浏览器弹窗时)
python .agent/skills/xiaohongshu-scraper/scripts/fetch_xhs.py --keywords "咖啡拉花教程" --headless
```

### 首次登录交互
小红书**必需登录**才能浏览内容：
1. 首次运行时，脚本会自动访问登录页，并截取二维码保存为 `xhs_qr_login.png`。
2. 脚本会在终端输出 `[!] 请扫码: <绝对路径>` 提示。
3. 用户扫码完成后，脚本会自动保存 state JSON，后续再调用即免登陆。

---

## 🤖 Agent 标准操作流

当用户请求"搜索/探索小红书某个主题"时，你应当执行以下步骤：

### 0. ⚠️ 检测扫码登录需求（关键！）

**运行脚本后，你必须立即检查命令输出**。如果输出中包含 `[!] 请扫码:` 字样，说明需要用户扫码登录。此时你必须：

1. **从输出中提取 QR 码图片的绝对路径**（例如 `P:\git_repos\llm_skills\xhs_qr_login.png`）
2. **立即用 `view_file` 工具读取该图片文件**，然后将图片展示给用户
3. **明确告知用户**：「请使用小红书 App 扫描此二维码登录，扫码后脚本会自动继续」
4. **等待脚本执行完成**——脚本会在用户扫码后自动保存 Cookie 并继续执行搜索任务

> 如果你不主动把二维码图片发给用户，用户将完全不知道需要扫码，脚本会一直等待直到超时退出！

**判断方法**：使用 `command_status` 检查脚本输出，关注是否包含以下关键词：
- `[!] 请扫码:` → 需要展示 QR 码
- `[*] 登录成功` → 扫码已完成
- `[✗] 扫码超时` → 超时失败，需重新运行

### 1. 扩充搜索词
根据用户的主题（例如“近期关于小米汽车的测评”），你需要推演出 2-3 个延伸的核心搜索词。
- 组合关键词：`"小米汽车测评,SU7提车作业,小米SU7驾驶体验"`

### 2. 执行抓取脚本
调用 `fetch_xhs.py` 获取原始数据。建议保存到临时 JSON。
注意：过程可能需要几分钟（为了防反爬，有随机秒数的 sleep）。
**启动脚本后立即按「步骤 0」检查是否需要扫码登录！**

### 3. 创建结果目录
抓取完成后，立刻构建专属的本地输出目录：
格式：`data/xiaohongshu/{主旨_格式化时间戳}/`
例如：`data/xiaohongshu/小米汽车测评_20260226_164000/`

### 4. 数据总结写入 (生成子 Markdown)
读取刚才的 JSON 结果。你会得到一个列表，每个元素包含：`url, title, content, author, date, interact_raw, comments` 等字段。

对于每个帖子内容，Agent 需要：
- 提炼 3-5 句精简的『主贴内容摘要』
- 基于其评论列表总结『评论区要点』(高频观点、有价值的讨论)

**为每个帖子创建独立的 Markdown 文件**写入目录，文件名格式：`{序号_2位}_{标题取前15字符}.md`。
文件内模板如下：
```markdown
# [原标题]

- **作者**: xxx
- **数据**: xxx赞 | xxx藏 | xxx评
- **发布日期**: xxx
- **原文链接**: [点击访问](url)

## 主贴内容摘要
[你提炼的内容]

## 评论区要点
[你提炼的结论，如果没有评论直接写“暂无有价值评论”]
```

### 5. 生成索引 `_index.md`
在这个新目录下，创建一个 `_index.md` 文件汇总这次检索。
模板建议：
```markdown
# 搜索任务: [主旨]

- **执行时间**: [YYYY-MM-DD HH:MM]
- **使用搜索词**: keyword1, keyword2
- **共抓取帖子**: [N] 篇

## 帖子导航目录
1. [帖子标题](./01_文件名.md) - *一句简短判语*
2. [帖子标题](./02_文件名.md) - *一句简短判语*
```

---

## ⚠️ 常见限制与故障排除
- **风控封禁**：脚本有等待延迟、加载翻页上限，尽量防止被小红书拉黑。因此**绝不要改动强行取消 script 中的延时**。
- **元素选择器失效**：如果抓出的标题为空，可能是小红书改版。检查 `scripts/selectors.py` 并借助调试功能重新寻找新类名。
- **二维码过期或等待超时**：脚本会异常退出，需让用户重新调用重试触发新的一轮扫码。
