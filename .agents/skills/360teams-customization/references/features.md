# 功能启停

## 命令

下列命令在 skill 目录运行，`--target` 使用现场发现的路径。

```powershell
node scripts/customize.cjs status --target 'S:\360 Teams\resources\app.asar'
node scripts/customize.cjs prepare --target 'S:\360 Teams\resources\app.asar' --qwork off
node scripts/customize.cjs apply --target 'S:\360 Teams\resources\app.asar'
```

开关接受 `on` 或 `off`：`--proxy`、`--qwork`、`--ai-minutes`。
未指定的开关保持当前状态。
`--proxy on` 让“系统默认”模式使用系统代理，实际端口由系统代理配置决定。
`--proxy off` 恢复原版代理逻辑。

例如启用 QWork 并保持 AI 灵记停用：

```powershell
node scripts/customize.cjs prepare --target 'S:\360 Teams\resources\app.asar' --qwork on --ai-minutes off
```

`prepare` 只生成候选包与安装前快照。
正常退出客户端后执行 `apply`，再启动并验收。
`restore` 恢复最近一次安装前快照。
恢复单项功能时，使用该功能的 `on` 开关。

## QWork

入口为 `dist/modules/qbot/index.js`。
停用时替换为受保护的状态查询接口，返回 `disabled=true`、`ready=false`、`shouldInject=false`。
后台运行组件不再初始化。
独立界面启动器隐藏 QWork 侧栏入口，并将其路由重定向到消息页。

验收状态查询、桥接返回值和侧栏可见性，确认没有 QWork webview。
用户数据保留在 `%USERPROFILE%/.deepbank` 与 `%APPDATA%/360Teams/qbot`。

## AI 灵记

入口为 `dist/aiMinutes/AiMinutesController.js`。
调用方为 `dist/openApi/api/aiMinutes.js`。
停用时控制器返回闲置和停用状态，录音与音频设置请求返回停用结果。
录音、转写、浮窗控制器与事件桥接不再初始化。
独立界面启动器隐藏 `aiMinutes` 侧栏入口，并阻止对应路由。

验收状态、录音操作返回值、侧栏可见性与 webview。
保留历史录音和纪要数据。
消息与审批页面需保持可用。

## 界面启动器

禁用模块时，`package.json` 的 `main` 指向 `dist/teams-customization.cjs`。
它注册主窗口界面处理后加载原 `dist/main.js`。
`dist/teams-customization.json` 记录需要关闭的路由。
处理范围限定为客户端本地 HTTP 主窗口。
全部模块启用时恢复原始 `package.json`，并移除这两个程序包内的辅助文件。
