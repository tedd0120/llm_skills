# 构建与完整性

当前适配 Windows 360Teams 5.6.6 的已验证构建。
版本号相同仍需校验程序包身份。
原版 SHA-256 为 `7bb8c74d5d80a7aaff62f31982feae619279df3a9c2538bb6d058215cdf6e2d4`。

## 初始化

从可信安装包或已保存备份取得原版 `app.asar`，明确传入路径：

```powershell
node scripts/customize.cjs init --target 'S:\360 Teams\resources\app.asar' --original-archive '<原版 app.asar>'
```

初始化将原版复制到本 skill 状态目录，并登记当前三个功能开关。
当前支持导入原版、已验证的系统代理补丁包，以及已验证的代理加 QWork 停用包。
既有 `360teams-proxy-repair` 备份可作为 `--original-archive` 来源。
旧状态目录保留供核查。
首次使用时，以状态目录中的 `state.json` 为功能状态来源。

## 校验

修改使用 `@electron/asar`，同时重建文件级 ASAR 校验信息与 `security/integrity-manifest.json`。
候选包逐文件比对，检查内容、unpacked 状态和应用完整性清单。
原生组件保持原内容。
启用嵌入式 ASAR 校验的可执行文件停止处理。
补丁保留原有签名与安全检查代码。

每次安装前保存当前包快照，并核对目标 SHA-256。
发生未登记修改时停止覆盖。
后续适配新构建时，重新检查初始化入口、全部调用方、共享接口与实际行为，再更新构建身份和补丁规则。

## 系统代理机制

原版 `dist/base/app.js` 根据 `NO_PROXY` 添加 `no-proxy-server`。
`dist/tools/NetworkDiagnostics.js` 随后可能应用 `auto` 会话策略。
系统代理补丁让这两处尊重 `network.appMode=system`。
修改用户 JSON 或增加启动参数前，先核实程序包中的代理覆盖逻辑。
独立 partition 与 Node.js 网络请求需要单独采集连接证据。
