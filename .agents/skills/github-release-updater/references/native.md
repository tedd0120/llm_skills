# 原生及其他桌面应用

按应用实际的打包与安装形态匹配对应分支。

## macOS 原生应用（Sparkle）

核查 Sparkle 与当前 `.app` Bundle 结构、App Sandbox 权限（如网络访问与外部进程拉起）及最低 macOS 系统版本的兼容性。客户端需在应用内集成 `SPUStandardUpdaterController` 并配置 feed 地址，与远端托管 `appcast.xml` 配套闭环。

- **Appcast 与资产托管：** 确定 `appcast.xml` 的稳定 HTTPS 地址、安装包下载地址、版本号字段与 EdDSA（ed25519）更新签名。GitHub Releases 托管安装包资产时，明确 `appcast.xml` 的生成时机与原子发布顺序；若仓库为私有，分别验证拉取 `appcast.xml` 与下载安装包资产的鉴权能力。
- **版本比较与双层签名：** 按锁定 Sparkle 版本的比较规则核对 `CFBundleVersion`（内部构建号）、`CFBundleShortVersionString`（展示版本）与更新通道（channel）。分别核查 Sparkle EdDSA 更新签名与 Apple Developer ID 签名、Hardened Runtime 及公证（Notarization）要求。

参考文档：[Sparkle 集成文档](https://sparkle-project.org/documentation/)、[Sparkle 更新安全](https://sparkle-project.org/documentation/security-and-reliability/)。

## .NET、C++、Rust、Python 桌面应用（Velopack）

- **打包与启动钩子：** 核对语言对应的 Velopack SDK、目标操作系统与架构、`vpk pack` 输入目录、程序入口启动钩子（处理安装、更新、卸载事件）、应用标识（`packId`）及既有安装目录布局。从传统安装包（如 MSI / Inno Setup / 单文件 EXE）迁移至 Velopack 时，设计清晰的引导安装路径，待用户完成首次迁移安装后接管后续自动更新。
- **GitHub Source 与安全校验：** 核对 `GithubSource` 对目标仓库、通道、预发布版本与私有仓 Access Token 的支持情况。确认 `releases.{channel}.json` 索引与 `.nupkg` 全量/差分包由当前 CLI 生成，并记录包完整性校验、系统代码签名与更新失败回滚的支持边界。
- **Python 冻结应用专项：** 额外核实 PyInstaller / Briefcase / Nuitka 的冻结入口、附带运行时资源路径及目标安装目录的写入权限。若目标环境缺少成熟的进程外替换方案且无法迁移至安装器形态，可设计“客户端检查远端 Release 版本并引导下载正式安装包”，同时在方案中明确标注未包含自动静默替换。

参考文档：[Velopack 文档](https://docs.velopack.io/)、[Update Sources 配置](https://docs.velopack.io/integrating/update-sources)、[打包与分发概览](https://docs.velopack.io/distributing/overview)。

## 应用商店、系统包管理器与便携版

- **商店与包管理器渠道：** Microsoft Store（MSIX）、Mac App Store、企业软件分发中心或系统包管理器（winget / Homebrew / apt）安装的应用，直接由对应渠道管理版本升级。方案中先核实渠道策略、包标识与权限边界，并在商店/包管理器构建包中关闭客户端自带的 GitHub Releases 更新检查。
- **绿色便携版（Portable）：** 核查当前所在目录的写入权限、运行中可执行文件占用锁（尤其是 Windows 下 `.exe` 与 `.dll` 锁定）、外部更新辅助进程（updater helper）交接逻辑以及替换中途失败的回滚机制。仅在成熟更新器无法满足便携形态约束时，才设计自定义外部替换进程，并如实列出跨平台文件锁与防病毒软件拦截的维护成本。
