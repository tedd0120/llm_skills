## 为什么

现有 skills 覆盖了金融数据（akshare API）和企业办公（Teams API）场景，但缺少社交媒体内容采集能力。小红书作为中国最大的生活方式分享平台，拥有大量高质量的用户生成内容（美妆、穿搭、家居、旅行、数码评测等），是进行消费洞察、舆情分析和趋势研究的重要数据源。

目前手动浏览小红书、逐帖阅读并总结内容效率低下。需要一个自动化 skill，能根据搜索主旨批量抓取帖子内容并由 AI 总结，持久化为本地 markdown 文件。

## 变更内容

- **新增 `xiaohongshu-scraper` skill**：基于 Python + Playwright 的浏览器自动化脚本，支持登录小红书、搜索关键词、抓取帖子正文与评论区文字内容
- **SKILL.md 引导 AI agent**：指导 agent 生成衍生搜索词、调用脚本、对抓取的原始文本进行 AI 总结、按帖子写入独立 .md 文件
- **Cookie 持久化**：首次 QR 码登录后保存浏览器状态，后续调用自动加载，无需重复登录
- **反风控机制**：随机延迟、帖子数上限（默认 10 / 最大 20）、评论加载限制，避免触发平台风控

## 功能 (Capabilities)

### 新增功能
- `xiaohongshu-browser-scraping`: 使用 Playwright 自动化浏览器访问小红书，完成登录、搜索、帖子内容与评论抓取
- `xiaohongshu-content-summarization`: AI agent 读取抓取的原始内容，生成帖子摘要，按搜索主旨组织为 markdown 文件集合

### 修改功能
（无）

## 影响

- **新增文件**：`.agent/skills/xiaohongshu-scraper/SKILL.md`、`scripts/fetch_xhs.py`、`scripts/selectors.py`
- **依赖**：`playwright`（需 `pip install playwright && playwright install`，或使用系统 Edge 浏览器 `channel="msedge"`）
- **环境配置**：`.env` 新增 `XHS_AUTH_STATE` 变量（Cookie 持久化路径）
- **跨平台**：Windows（有头 msedge）、Linux（Xvfb 或 headless + stealth）
- **Agent 兼容**：脚本本身不依赖任何 agent 框架，Antigravity / OpenClaw / CLI 均可调用
