## 为什么

当前编排层在调用 `login_xhs.py` 时使用阻塞模式。未登录场景下，脚本会生成二维码并等待扫码，但 Agent 在命令返回前无法发送对话提示，用户通常需要自行到目录中查找二维码图片，流程可见性差且容易超时。

## 变更内容

- 将 scraper 执行阶段中的“确保登录”步骤调整为后台运行 + 轮询状态模式。
- 增加登录轮询间隔配置项，允许在不同环境下调整轮询频率。
- 规定当检测到 `NEED_LOGIN:<path>` 时，Agent 必须立即提示用户扫码，并展示二维码图片绝对路径。
- 保留现有登录结果语义（`LOGIN_OK` / `LOGIN_SUCCESS` / `LOGIN_TIMEOUT` / `LOGIN_FAILED`），不引入新状态码。

## 功能 (Capabilities)

### 新增功能
- `xiaohongshu-scraper`: 登录步骤支持后台状态轮询，并在需要扫码时主动提示二维码路径。

### 修改功能
- `xhs-login`: 明确 `NEED_LOGIN` 事件需在等待扫码前输出，且路径需为绝对路径，便于编排层直接提示用户。

## 影响

- 受影响规范：`openspec/specs/xiaohongshu-scraper/spec.md`、`openspec/specs/xhs-login/spec.md`
- 受影响文档/流程：`.claude/skills/xiaohongshu-scraper/SKILL.md` 的登录执行步骤
- 不改变抓取、总结、格式化阶段的输入输出格式
