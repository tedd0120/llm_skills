# Windows 分类与复核

规则写在 `scripts/analyze.py`，按以下顺序匹配，每个文件只归入一组。

| 顺序 | 规则 | 分类 | 等级 | 复核要点 |
| --- | --- | --- | --- | --- |
| 1 | `AppData\Local\Temp` 中超过 `--temp-days` 天的文件 | 临时文件与日志 | 优先清理 | 被占用的文件清理时自动跳过 |
| 2 | 已知工具目录：npm、pip、uv、pnpm、Yarn、Go 构建、Electron、Cargo、Poetry 下载缓存 | 开发工具缓存 | 优先清理 | 下次安装或构建时重新下载 |
| 2 | Gradle、Maven、NuGet、Go 模块、Hugging Face、conda、nexe、Poetry 虚拟环境 | 开发工具缓存 | 需确认 | 重新下载耗时长，或包含环境本身 |
| 2 | 夸克视频缓存、Spotify 音频缓存 | 媒体与聊天缓存 | 需确认 | 资源下架后无法找回 |
| 2 | 微信日志、CrashDumps、WER、OneDrive 日志、INetCache、D3DSCache | 临时文件与日志 / 应用缓存 | 优先清理 | 诊断材料，不含用户数据 |
| 3 | 同一父目录下的多个版本：Playwright、Puppeteer、Codeium 浏览器，Squirrel `app-*`，Claude Code 版本，OneDrive 版本，`*\runtimes\<工具>\<版本>` | 旧版本与安装包 | 需确认 | 保留最新版本；核对项目是否固定旧版本 |
| 4 | `xwechat_files\<账号>\cache` | 媒体与聊天缓存 | 需确认 | 过期图片视频可能无法重新下载 |
| 5 | `Downloads` 中 30 天前的安装包、镜像、压缩包 | 旧版本与安装包 | 需确认 | 压缩包可能是唯一副本 |
| 6 | `*-updater` 目录的安装包、夸克 updates、Squirrel `packages\*.nupkg` | 旧版本与安装包 | 需确认 | 等待安装的更新需重新下载 |
| 7 | Chrome 等的 `OptGuideOnDeviceModel` | 浏览器与应用缓存 | 需确认 | 功能开启时浏览器会重新下载 |
| 8 | AppData 下的缓存目录名：Cache、Code Cache、GPUCache、各类 ShaderCache、Service Worker 的 CacheStorage 和 ScriptCache、CachedData、component_crx_cache 等 | 浏览器与应用缓存 | 优先清理 | 按应用合并为一组；`parts` 列出各缓存位置 |
| 8 | Crashpad 目录 | 临时文件与日志 | 优先清理 | 与应用日志合并为“日志与崩溃报告” |
| 9 | AppData 下 `logs`/`log` 目录中 3 天前的 `.log`、`.etl`、`.dmp`、`.old` | 临时文件与日志 | 优先清理 | 只取日志扩展名 |

路径上含 `node_modules`、`site-packages`、`vendor`、`src` 的文件跳过第 7–9 条，避免把代码依赖中的同名目录当成缓存。云端占位文件不进入候选。MSIX 应用在 `Packages\<包>\LocalCache` 与 `AppData` 下会呈现同一份文件，分组时只保留 `AppData` 路径。

## 复核

名称含 Cache 只是线索。通用规则（第 8 条）命中陌生应用时，查看 `parts` 和样例文件：内容是下载的视频、离线文档或模型时，在决策文件中改为“需确认”或停用。代码依赖、工具链、聊天记录、文档不进入可清理分组，它们出现在“需要你判断的大目录”中，只提供打开和处理建议。

每个“需确认”组写清内容、核对入口和清理后的影响。普通应用本体按正常占用展示，只有重复版本等具体决策才列为候选。

## 系统空间

| 卡片 | 来源 | 网页操作 |
| --- | --- | --- |
| 回收站 | `$Recycle.Bin`，网页实时查询大小 | 打开回收站、清空回收站（Windows 再确认） |
| 休眠文件 | `hiberfil.sys` | `powercfg /h /type reduced`、`powercfg /h off`（管理员） |
| Windows 更新残留 | `SoftwareDistribution.old.*`、`SoftwareDistribution\Download`、`$WINDOWS.~BT`、`$WinREAgent`、`Windows.old`、`Windows\Temp`、系统 WER | 磁盘清理 `cleanmgr /d C:`、删除旧更新目录（管理员） |
| 组件存储 | `WinSxS`，硬链接使显示值偏大 | `Dism /Online /Cleanup-Image /StartComponentCleanup`（管理员） |
| 虚拟内存 | `pagefile.sys`、`swapfile.sys` | 打开性能选项；有其他盘时给出迁移步骤 |
| Store 应用、安装程序缓存 | `WindowsApps`、`Installer`、`Package Cache` | 打开已安装的应用 |
| 存储感知 | — | 打开存储设置 |

回收站、休眠文件和更新残留计入“系统级可回收”，其余卡片只作说明。

## 覆盖范围

重解析点、云占位文件和无权限目录不扫描，空间分布根目录显示“无权限读取的系统区域”的差额。统计使用逻辑大小，硬链接可能重复计数。不做文件内容哈希去重。
