# 已验证的补丁机制

2026-10-19 本机 5.6.6 构建有两处代理覆盖：

- `dist/base/app.js` 根据包内 `NO_PROXY` 添加 `no-proxy-server`。用户配置的 `network.appMode=system` 不参与原判断。
- `dist/tools/NetworkDiagnostics.js` 后续执行 `network.mode=auto`，可再次改变默认会话代理配置。

补丁让启动判断尊重 `network.appMode=system`，并在该模式下显式执行 `session.defaultSession.setProxy({mode:'system'})`。服务直连分支保持原行为。

`configInfo.NO_PROXY` 是记录值，源值来自程序包配置。仅编辑用户 JSON 或追加 `--proxy-server` 不能可靠解除启动开关。INI 字符串 `"false"` 仍可能被 JavaScript 判断为真。

## 完整性

包包含 ASAR 的文件完整性元数据，以及 `security/integrity-manifest.json`。修改文件后需更新两层哈希。脚本保留校验执行逻辑，重新验证应用清单中的全部文件。

可执行文件若启用嵌入式 ASAR 完整性检查，脚本停止。需要签名授权的构建应走维护者支持的发布流程。

## 新构建适配

精确语句匹配失败时，先只读检查实际启动路径、会话设置及调用时序。更新补丁锚点前确认功能含义一致。重建候选包并重新完成完整性与客户端验收。

当前补丁只调整默认浏览器会话。独立 partition 或 Node.js 原生网络请求需要额外证据，按实际请求入口处理。

## Windows 界面操作

使用现场可用的 computer-use 技能或浏览器调试工具。Ctrl+Q 退出框可能是独立窗口，优先重新获取窗口和截图后操作。隐藏启动导致窗口无法点击时，可再次正常启动同一应用唤起已有窗口。

Clash 控制接口凭据仅在内存中使用。保存主机名、规则和节点链路即可，不导出完整连接元数据或认证配置。
