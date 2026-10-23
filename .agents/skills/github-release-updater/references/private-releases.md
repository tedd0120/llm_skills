# 私有 GitHub Releases 鉴权

## 凭据边界与分发模型

CI 发布凭据与客户端读取凭据严格分离：CI 使用具备 Release 写入权限的令牌；客户端仅需目标仓库的 Release 资产只读权限。本机 `git` 或 `gh` CLI 的登录态与桌面应用运行态相互独立。

- **内部或自用工具：** 由用户在客户端内录入个人 PAT。
- **对外分发的商业或团队软件：** 每台客户端使用接收方自有凭据，维护者 PAT 严禁内置进安装包。GitHub 仓库读取权限等同于源码访问权限；当接收方不应拥有源码读取权时，在方案中指明单靠源码仓 Releases 的权限边界，改为评估独立公开/私有分发仓库（仅放构建产物）或前置鉴权网关。
- **Token 类型选择：** 优先使用 Fine-grained PAT，仅授予目标仓库 `Contents: Read-only` 权限；若勾选 `All repositories` 则同时开放同账户/组织下全部仓库的源码读取，需在方案中显式说明。Classic PAT 的 `repo` 范围包含写权限，仅在目标环境确有兼容要求时选用。仓库归属组织时，额外核查组织级 PAT 审批、SSO 授权与过期策略。

参考文档：[PAT 管理与权限范围](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)、[Release 资产下载接口](https://docs.github.com/en/rest/releases/assets#get-a-release-asset)。

## 凭据存储与设置界面

复用项目已有的系统凭据库（Windows Credential Manager / macOS Keychain / Linux Secret Service）存储敏感凭据。普通配置文件仅存非敏感开关；前端界面仅读取“凭据是否已配置”布尔状态与最近一次验证结果。用户 Token、签名私钥与含密钥参数的预签名 URL 严禁出现在日志、IPC 事件、崩溃报告或方案文档中。

凭据生命周期与交互状态：

1. **校验与保存：** 保存前裁剪首尾空白，拒绝空串与非法的 HTTP Header 字符；写入系统凭据库后立即清空输入框，重开设置页仅展示“已保存”状态。
2. **真实请求核验：** 保存成功后立即发起一次真实更新检查，以接口实际响应确认权限有效。
3. **替换与清除：** 用户替换或清除 Token 时，立即中止进行中的检查与下载任务，并丢弃旧任务的迟到回调。已落盘且通过签名校验的安装包是否保留，按产品策略、版本与通道决定。
4. **异常呈现：** 区分凭据库写入失败、Token 无效/过期（401）、权限不足（403）与仓库不可达（404）。

## 元数据与资产请求链路

优先使用所选更新器内置的私有 GitHub provider。需要自定义或接管下载链路时，按以下四步闭环设计：

1. 请求 GitHub API 获取目标通道的 Release 元数据。
2. 在同一 Release 响应中锁定更新清单、当前平台/架构的安装包与签名资产 ID。
3. 请求 Release Asset API（设置 `Accept: application/octet-stream`），兼容直接返回字节流与 `302/307` HTTPS 重定向至对象存储。
4. 核对 Release 标签、清单内版本号、目标架构与签名。私有仓库全链路走 API 鉴权请求（公开下载链接 `browser_download_url` 仅用于公开仓库）。

**重定向与代理安全约束：**

- **敏感请求头剥离：** `Authorization` 仅发送给预期的 GitHub API origin（含协议、主机名与端口）。限制最大重定向跳数并阻断 HTTPS 降级；发生跨 origin 跳转（如 GitHub API 跳转至临时对象存储域名）时，立即移除 `Authorization` 与 `Cookie`，且后续跳转保持移除状态。
- **代理一致性：** 逐一核实项目自定义元数据客户端、更新器清单客户端与安装包下载客户端的代理配置。显式定义代理配置为空时的行为（直连或跟随系统/环境变量代理）；若规定为空即直连，需在 HTTP 客户端中显式关闭环境变量代理继承。代理连接失败时直接向用户报错，保持网络出口唯一。

## HTTP 状态码与用户反馈映射

| 阶段或响应特征 | 向用户展示的明确反馈与可执行操作 |
|---|---|
| 元数据请求返回 `401` | 凭据无效或已过期，引导用户重新录入或替换 Token |
| 返回 `403` / `429`，且 `x-ratelimit-remaining: 0` 或含 `Retry-After` | 触发 GitHub 速率限制，按响应头提示等待时间（同步核查 secondary rate limit 响应特征） |
| 其他 `403` | 当前 Token 无权访问该仓库（排查仓库权限、Fine-grained 范围、组织审批或 SSO 授权） |
| 私有资源返回 `404` | 目标 Release / 资产不存在，或当前 Token 无权读取该私有仓库 |
| 更新器插件合并后的清单报错 | 远端发布产物缺失或不可达，仅展示插件实际返回的确定信息 |
| 无结构化状态码的下载异常 | 按所处阶段（检查 / 下载 / 验签）区分网络中断、超时、用户取消与验签失败，基于阶段枚举而非英文报错文本分类 |

参考文档：[GitHub REST API 错误与限流排查](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)。
