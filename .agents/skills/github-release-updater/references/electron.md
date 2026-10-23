# Electron

读取 `package.json`、依赖锁文件、主进程入口、`preload` 脚本与打包配置。明确区分 Electron 内置的 `autoUpdater`（基于 Squirrel）与 `electron-updater`（配套 `electron-builder`）。若项目当前使用 Electron Forge 或 Squirrel，单独核实其更新协议、产物形态与切向 `electron-builder` 的迁移代价。

## 选型与配置核查

- **打包目标与安装形态：** `electron-builder` 项目优先选用配套的 `electron-updater`，逐平台核实当前 target 是否支持自动更新（例如 Windows 下 NSIS 安装版支持自动更新，portable 便携版无内置自动替换生命周期；macOS 需同时产物 `.dmg` 与 `.zip`）。
- **Provider 与凭据注入：** 查明 `publish` 配置（provider、owner、repo、channel）如何生成并打入 `app-update.yml`。按锁定的 `electron-updater` 版本核实公开仓与私有仓 GitHub provider 的 Token 传入方式（如 `requestHeaders` 或私有 token 配置项）。
- **产物清单与差分包：** 清单（`latest.yml` / `latest-mac.yml` / `latest-linux.yml`）、安装包与 `.blockmap` 差分文件均由 `electron-builder` 生成。按实际构建输出列出产物文件名，并明确 `.blockmap` 缺失或差分失败时回退全量下载的行为。
- **进程职责隔离：** 主进程独占更新器实例与读取凭据；渲染进程仅通过 preload 暴露的窄 IPC 接口订阅状态、下载进度并触发检查或安装。
- **检查、下载与安装解耦：** 对照锁定版本核实 `autoDownload`、`autoInstallOnAppQuit`、显式调用 `quitAndInstall(isSilent, isForceRunAfter)` 的行为差异。文档中的新字段需在本地锁定的 `node_modules` 类型与源码中确认已受支持。
- **双层签名与系统交互：** 分别核实 `electron-updater` 的发布者名称/证书校验与操作系统级代码签名（macOS Developer ID 签名与公证、Windows Authenticode 证书与 UAC 提权弹窗）。跨主版本升级 `electron-builder` 时，查阅对应版本的签名校验变更说明。

## 运行时与迁移审查重点

- **窗口关闭与进程退出：** 核查点击窗口关闭按钮是隐藏至系统托盘还是真正退出；检查 `window-all-closed`、`before-quit`、`will-quit` 中的拦截逻辑是否阻塞 `quitAndInstall`；确保业务数据库刷盘与子进程回收完成后再拉起安装器。
- **私有仓库全链路鉴权：** 优先复用 `electron-updater` 内置的 GitHub 私有仓支持，验证更新清单、安装包与 `.blockmap` 三类请求均携带正确鉴权头且跨源重定向安全。
- **打包态验收与迁移过渡：** 开发模式（`dev-app-update.yml`）仅用于调试检查逻辑，最终验收必须使用正式打包安装后的客户端。更换打包器、修改 `appId` 或更换签名证书时，为存量用户设计过渡版本或首次手动覆盖安装路径。

## 官方文档

按项目锁定的 `electron-builder` 主版本查阅对应文档：

- [electron-builder Auto Update（最新版）](https://www.electron.build/docs/features/auto-update/)
- [electron-builder v26 Auto Update](https://www.electron.build/v26/docs/features/auto-update/)
- [electron-builder Security](https://www.electron.build/docs/features/security/)
- [Electron 内置 autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater)
