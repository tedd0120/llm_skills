## 为什么

当前小红书 scraper 的登录逻辑嵌入在搜索脚本中。当用户扫码登录时，Python 脚本阻塞执行，Agent 只能在脚本结束后才能检测到需要扫码，导致用户错过扫码窗口而超时失败。

将登录和搜索分离后，Agent 可以在检测到需要登录时立即展示二维码给用户，显著改善用户体验。

## 变更内容

**新增**：
- `xiaohongshu-login` skill：独立处理小红书登录、Cookie 验证和保存
- `scripts/login_xhs.py`：支持 `--check-only`（验证 Cookie）和登录模式（显示二维码、等待扫码）

**修改**：
- `xiaohongshu-scraper` skill：移除内置的登录逻辑，假设已登录状态
- `scripts/fetch_xhs.py`：移除 `_ensure_login` 方法，简化为纯搜索脚本
- Agent 执行流程：在步骤 1（澄清）和步骤 2（创建目录）之间插入"确保已登录"步骤

**BREAKING**：
- `fetch_xhs.py` 不再自动处理登录，用户必须先通过 `xiaohongshu-login` skill 登录

## 功能 (Capabilities)

### 新增功能
- `xhs-login`: 小红书登录和 Cookie 管理功能，包括登录状态检查、二维码登录、Cookie 保存和验证

### 修改功能
- `xhs-scraper`: 小红书内容抓取功能，移除登录处理逻辑，依赖外部提供的有效 Cookie

## 影响

**新增文件**：
- `.claude/skills/xiaohongshu-login/SKILL.md`
- `.claude/skills/xiaohongshu-login/scripts/login_xhs.py`

**修改文件**：
- `.claude/skills/xiaohongshu-scraper/SKILL.md`
- `.claude/skills/xiaohongshu-scraper/scripts/fetch_xhs.py`

**依赖**：
- Playwright（已有）
- 小红书登录流程
