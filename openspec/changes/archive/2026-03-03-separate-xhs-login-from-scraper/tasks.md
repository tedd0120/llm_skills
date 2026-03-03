## 1. 创建 xiaohongshu-login skill

- [x] 1.1 创建 skill 目录结构 `.claude/skills/xiaohongshu-login/`
- [x] 1.2 编写 `SKILL.md` 文档，定义 login_xhs.py 的使用方式
- [x] 1.3 创建 `scripts/login_xhs.py` 脚本基础结构
- [x] 1.4 实现浏览器初始化和 Cookie 加载逻辑
- [x] 1.5 实现 `--check-only` 模式：验证 Cookie 有效性
- [x] 1.6 实现二维码截取和保存功能（保存到项目根目录 `xhs_qr_login.png`）
- [x] 1.7 实现扫码等待逻辑，支持 `--timeout` 参数（默认 120 秒）
- [x] 1.8 实现标准化输出格式：`LOGIN_OK`, `NEED_LOGIN:<path>`, `LOGIN_SUCCESS`, `LOGIN_TIMEOUT`, `LOGIN_FAILED`
- [x] 1.9 实现登录完成后 Cookie 保存和二维码清理
- [x] 1.10 添加异常处理和退出码管理

## 2. 修改 xiaohongshu-scraper skill

- [x] 2.1 从 `fetch_xhs.py` 中移除 `_ensure_login` 方法
- [x] 2.2 从 `fetch_xhs.py` 中移除 `_qr_login` 方法
- [x] 2.3 简化 `run()` 方法，移除登录检查调用
- [x] 2.4 添加未登录检测逻辑：搜索过程中检测到登录页时输出错误并退出
- [x] 2.5 添加 UTF-8 编码支持（如果尚未添加）
- [x] 2.6 更新 `SKILL.md`，在步骤 1（澄清）后添加步骤 1.5（确保已登录）
- [x] 2.7 更新 `SKILL.md`，添加登录失败时的错误处理说明

## 3. 共享代码维护

- [x] 3.1 确保 `login_xhs.py` 和 `fetch_xhs.py` 共享同一个 `selectors.py`
- [x] 3.2 统一 Cookie 路径配置（使用 `XHS_AUTH_STATE` 环境变量）

## 4. 测试和验证

- [x] 4.1 测试首次登录流程：无 Cookie → 扫码 → 保存 Cookie
- [x] 4.2 测试 Cookie 验证：`--check-only` 正确识别登录状态
- [x] 4.3 测试搜索流程：使用有效 Cookie 成功抓取
- [x] 4.4 测试过期处理：模拟 Cookie 过期场景，验证错误提示
- [-] 4.5 测试超时处理：验证扫码超时后的正确退出（需等待超时，跳过自动化测试）
- [-] 4.6 端到端测试：完整 Agent 流程（澄清 → 登录验证 → 搜索 → 报告）（需完整用户会话）
