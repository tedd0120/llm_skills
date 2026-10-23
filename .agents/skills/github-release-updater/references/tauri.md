# Tauri

读取 `Cargo.lock`、前端锁文件、`tauri.conf.json`、平台覆盖配置、`capabilities`（权限声明）与 Rust 启动入口。先区分 Tauri v1 与 Tauri v2，并查明当前更新调用发自前端 JS 插件还是 Rust 后端服务，据此划定权限与凭据边界。

## 架构与配置要点

- **产物与配置绑定：** 更新签名包、公钥（`pubkey`）、`endpoints`、平台 target key（如 `windows-x86_64`、`darwin-aarch64`）及安装模式（如 Windows NSIS / MSI 的 `installMode`）由 Tauri CLI、`tauri-plugin-updater` 与构建 Action 共同决定。
- **签名密钥管理：** 为 Tauri updater 专用的 minisign 私钥制定 CI Secret 注入、安全备份与密钥轮换方案。
- **公开与私有仓库分流：** 公开仓库可直接使用 GitHub Releases 静态 `latest.json` 清单地址；私有仓库需核实插件能否为清单请求与资产包下载分别配置 GitHub Asset API 地址、`Accept` / `Authorization` 请求头及代理。
- **Rust 端收口管理：** 私有凭据由 Rust 服务从系统凭据库读取。由 Rust 统一接管更新生命周期时，排查前端 `@tauri-apps/plugin-updater`、旧版 IPC 命令与 `capabilities` 权限声明是否仍有残留调用方。
- **Windows 强制退出与资源清理：** Windows 安装器拉起时可能直接终止宿主进程；关闭数据库连接、刷盘日志与终止子进程的清理逻辑，必须挂载在插件源码实际执行的退出前钩子上。

## 依赖源码核查清单

以下源码线索基于 `tauri-plugin-updater 2.10.1` 核实；项目锁定其他版本时，须在本地 `Cargo.lock` 对应的源码中重新核对：

| 源码符号 / 位置 | 方案必须回答的技术问题 |
|---|---|
| `UpdaterBuilder::configure_client` | 插件内部自建 `reqwest::Client`：项目的代理配置、HTTPS 限制与跨源重定向规则如何同时注入检查与下载两条路径？插件依赖的 `reqwest` 版本与项目主工程是否一致？ |
| `UpdaterBuilder::timeout` / `Update.timeout` | 构建器设置的检查超时会继承给返回的 `Update` 对象；若需为大体积安装包单独延长下载超时，是否在 `check()` 返回后覆写 `Update.timeout`？ |
| `Updater::check` 错误分支 | 远端返回 `401` / `403` / `404` 时是否被插件统一折叠为 `ReleaseNotFound`？哪一步请求还能拿到原始 HTTP 状态码？ |
| `Error::Network` | 下载阶段报错是否仅保留格式化字符串？缺少结构化状态码时，如何按所处阶段定义自有错误码？ |
| `UpdaterBuilder::on_before_exit` | Windows 触发安装前同步执行的清理回调是哪一个？常规的 Tauri `RunEvent::ExitRequested` 能否被触发？ |
| 版本比较与清单解析 | 远端无新版本时插件是否依然拉取并解析清单？Release 标签与清单内 `version` 字段的一致性校验放在哪一层？ |

项目自定义的 GitHub API 元数据预检请求与 `tauri-plugin-updater` 内部请求需分别设计错误映射。跨 origin 重定向剥离 `Authorization` 必须有真实客户端行为或测试抓包证据（`reqwest` 的 `redirect::Policy` 本身仅控制是否跟随跳转）。

使用挂载本地受信测试 CA 的 HTTPS 模拟服务与虚构 Token，完整验证插件的检查、下载、跨源跳转、版本比对、验签与错误分支。

## 官方文档

优先以本机锁定的 crate 源码为准，主分支文档作对照参考：

- [Tauri v2 Updater 插件文档](https://v2.tauri.app/plugin/updater/)
- [tauri-action 发布配置](https://github.com/tauri-apps/tauri-action)
- [plugins-workspace 仓库（v2 updater）](https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/updater)
- [tauri-plugin-updater 2.10.1 源码（docs.rs）](https://docs.rs/tauri-plugin-updater/2.10.1/src/tauri_plugin_updater/updater.rs.html)
