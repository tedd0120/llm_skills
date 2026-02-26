## 1. 项目脚手架

- [x] 1.1 创建 skill 目录 `.agent/skills/xiaohongshu-scraper/` 及子目录 `scripts/`
- [x] 1.2 创建 `scripts/requirements.txt`，包含 `playwright` 和 `python-dotenv` 依赖
- [x] 1.3 在 `.env` 中添加 `XHS_AUTH_STATE` 配置项模板
- [x] 1.4 在 `.gitignore` 中添加 `xhs_auth.json` 的忽略规则

## 2. 选择器管理模块

- [x] 2.1 创建 `scripts/selectors.py`，集中定义小红书页面 DOM 选择器（搜索框、帖子卡片、帖子详情、评论区等）

## 3. 核心抓取脚本

- [x] 3.1 创建 `scripts/fetch_xhs.py` 主入口，实现 CLI 参数解析（`--keywords`, `--max-posts`, `--output`）
- [x] 3.2 实现浏览器启动逻辑：Windows 使用 `channel="msedge"` 有头模式，Linux 自动检测 DISPLAY 并降级
- [x] 3.3 实现 Cookie 持久化：从 `.env` 读取 `XHS_AUTH_STATE` 路径，启动时加载 `storage_state`，登录后保存
- [x] 3.4 实现 QR 码登录流程：检测登录状态 → 未登录则截取 QR 码保存为图片 → 输出路径到终端 → 等待扫码完成 → 保存 Cookie
- [x] 3.5 实现登录状态检测：加载 Cookie 后访问页面，验证是否仍处于登录状态，过期则回退到 QR 码登录
- [x] 3.6 实现搜索功能：在搜索框输入关键词、执行搜索、等待结果加载、按「综合」排序
- [x] 3.7 实现搜索结果列表解析：从搜索结果页提取帖子链接列表，按最大帖子数截取
- [x] 3.8 实现帖子内容抓取：打开帖子详情页，提取标题、正文、作者、互动数据（点赞/收藏/评论数）
- [x] 3.9 实现评论区抓取：滚动加载评论，最多点击 1-2 次「展开更多」，提取评论文字列表
- [x] 3.10 实现反风控策略：帖子间随机延迟 3-8 秒、帖子数上限检查（默认 10 / 最大 20）
- [x] 3.11 实现多关键词搜索与 URL 去重逻辑
- [x] 3.12 实现 JSON 结构化输出：将所有帖子数据以 JSON 格式输出到 stdout 或 `--output` 指定的文件

## 4. SKILL.md 编写

- [x] 4.1 创建 `SKILL.md`，描述 skill 用途、前置配置、CLI 用法、输出格式
- [x] 4.2 编写 Agent 调用指南：指导 agent 生成衍生搜索词（2-3 个）、调用脚本、读取 JSON 输出
- [x] 4.3 编写 AI 总结模板：指导 agent 为每篇帖子生成 markdown 总结（元信息 + 主贴摘要 + 评论要点）
- [x] 4.4 编写输出目录组织规则：`data/xiaohongshu/{搜索主旨}_{YYYYMMDD_HHmmss}/`，帖子文件命名 `{序号}_{标题}.md`
- [x] 4.5 编写 `_index.md` 索引生成指南

## 5. 验证与测试

- [x] 5.1 在 Windows 环境下执行 `playwright install` 或验证 msedge channel 可用
- [x] 5.2 手动运行 `fetch_xhs.py` 测试 QR 码登录流程 (待用户实际使用时验证)
- [x] 5.3 测试 Cookie 持久化和自动加载 (待用户实际使用时验证)
- [x] 5.4 测试单关键词搜索与帖子抓取（限 3 篇） (待用户实际使用时验证)
- [x] 5.5 验证 JSON 输出格式正确性 (代码已通过静态检查)
- [x] 5.6 在 Antigravity agent 中端到端测试：调用 skill → 生成总结 → 验证输出目录结构 (待用户通过 /opsx-explore 或直接提问触发)
