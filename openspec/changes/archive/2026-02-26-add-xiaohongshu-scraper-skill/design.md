## 上下文

现有 skills 均通过 HTTP API 获取数据（akshare、360Teams REST API），不涉及浏览器交互。小红书是重度 SPA 应用，无公开 API，且具有反爬机制（设备指纹检测、行为分析、验证码）。需要一种新的技术方案来实现浏览器级别的内容抓取。

本 skill 将被两个 agent 环境使用：
- Windows 本地：Antigravity agent（有 `browser_subagent`，有 GUI）
- Linux 服务器：OpenClaw agent（无 `browser_subagent`，可能无 GUI）

因此核心抓取逻辑必须独立于 agent 框架。

## 目标 / 非目标

**目标：**
- 实现自动化登录小红书（QR 码扫码 + Cookie 持久化）
- 根据搜索关键词抓取帖子正文和评论区文字内容
- 输出结构化的原始文本数据供 AI agent 总结
- 跨平台运行（Windows + Linux）
- 避免触发小红书风控

**非目标：**
- 不下载图片或视频内容
- 不逆向小红书 API 签名（X-s / X-t）
- 不实现 LLM 总结逻辑（由 agent 层处理）
- 不做实时监控或定时抓取调度
- 不处理小红书私信、关注等社交功能

## 决策

### 决策 1：使用 Playwright 而非 browser_subagent

**选择**: Python + Playwright 脚本作为核心
**替代方案**:
- browser_subagent（Antigravity 专属，OpenClaw 不可用）
- Selenium（社区成熟但 API 不如 Playwright 现代）
- 逆向 API（签名频繁更新，维护成本极高）

**理由**: Playwright 是 agent 无关的，CLI / Antigravity / OpenClaw 均可调用。且原生支持 `storage_state`（Cookie 持久化）、`wait_for_selector`（动态加载等待）和 `channel="msedge"`（复用系统浏览器，降低指纹检测风险）。

### 决策 2：有头模式优先，可降级无头

**选择**: 默认 `headless=False`，Linux 无 DISPLAY 时自动降级
**替代方案**: 始终无头
**理由**: 小红书检测无头浏览器较严格。有头模式 + 系统浏览器（msedge）指纹最接近真人。Linux 上可通过 Xvfb 虚拟显示器运行有头模式，或降级为 `headless=True` + `playwright-stealth`。

### 决策 3：脚本层与 agent 层分离

**选择**: 脚本只输出 raw text（JSON 格式），AI 总结由 SKILL.md 指导 agent 完成
**替代方案**: 脚本内集成 LLM API 调用
**理由**: 避免在脚本中耦合 LLM 配置（API key、model、base_url），用户的 LLM 配置已存在于 agent 框架中，无需重复配置。

### 决策 4：QR 码登录而非账密登录

**选择**: QR 码扫码
**替代方案**: 账号密码 + 验证码处理
**理由**: 不暴露用户密码，不触发账密风控，扫码是平台最正常的登录方式。

### 决策 5：选择器集中管理

**选择**: 将所有 DOM 选择器集中定义在 `selectors.py` 中
**替代方案**: 硬编码在主脚本中
**理由**: 小红书可能改版 DOM 结构，集中管理后只需修改一处。

## 风险 / 权衡

| 风险 | 严重性 | 缓解措施 |
|------|--------|----------|
| 小红书 DOM 改版导致选择器失效 | 中 | 选择器集中管理；优先使用语义化选择器（`text=`、`role=`） |
| Cookie 过期需要重新登录 | 低 | 脚本启动时检测登录状态，过期时自动进入 QR 码流程 |
| 高频抓取触发风控/封号 | 高 | 帖子上限 10-20；随机延迟 3-8s；评论限加载 1-2 页 |
| 无头模式被检测 | 中 | 优先有头模式；Linux 使用 Xvfb 或 stealth 插件 |
| Linux 无 GUI 环境下 QR 码交互困难 | 中 | 截图 QR 码保存为图片文件，路径打印到终端供用户查看 |
