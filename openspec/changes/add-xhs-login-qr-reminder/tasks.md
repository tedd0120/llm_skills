## 1. 规范与文档

- [x] 1.1 新增 `xhs-login` 增量规范：扫码路径输出时序和绝对路径要求
- [x] 1.2 新增 `xiaohongshu-scraper` 增量规范：登录后台轮询与扫码提醒要求
- [x] 1.3 更新 `xiaohongshu-scraper/SKILL.md` 登录步骤说明，加入 `LOGIN_POLL_INTERVAL_SEC` 配置项

## 2. 实现

- [x] 2.1 将“确保登录”步骤改为后台执行登录脚本
- [x] 2.2 增加登录输出轮询逻辑，并按 `LOGIN_POLL_INTERVAL_SEC` 间隔检查
- [x] 2.3 解析到 `NEED_LOGIN:<abs_path>` 时，向用户发送扫码提示并展示绝对路径
- [x] 2.4 处理 `LOGIN_OK` / `LOGIN_SUCCESS` / `LOGIN_TIMEOUT` / `LOGIN_FAILED` 收敛逻辑

## 3. 验证

- [x] 3.1 验证未登录场景：能在扫码等待期间收到提示且路径可用
- [x] 3.2 验证已登录场景：无需扫码，登录步骤快速通过
- [x] 3.3 验证超时/失败场景：正确报错并停止后续流程
- [x] 3.4 验证轮询间隔配置：默认值、合法值、非法值回退
