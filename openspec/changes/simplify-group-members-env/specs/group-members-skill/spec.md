# 功能：group-members-skill

## 修改需求

### 需求：移除冗余的 TEAMS_COOKIE 环境变量依赖

脚本**必须**仅依赖 `TEAMS_AUTHORIZATION` 环境变量进行认证，**禁止**要求配置 `TEAMS_COOKIE`。API 测试验证 `Cookie` 请求头对群组成员查询接口完全多余。

#### 场景：仅使用 Authorization 获取群组成员

- 当 `.env` 中仅配置了 `TEAMS_AUTHORIZATION`（无 `TEAMS_COOKIE`）
- 调用 `fetch_group_members("FhSnheH3T_grT5yzxqVS5o")`
- **必须**返回完整的成员列表，API 返回 code=0

#### 场景：函数签名不包含 cookie 参数

- `fetch_group_members` 函数**必须**仅接受 `group_code`、`authorization`、`verbose` 参数
- **禁止**包含 `cookie` 参数

#### 场景：环境变量检查仅验证 TEAMS_AUTHORIZATION

- 当 `.env` 中未配置 `TEAMS_AUTHORIZATION` 时
- `_check_env()` **必须**抛出 `EnvironmentError`，提示缺少 `TEAMS_AUTHORIZATION`
- **禁止**检查 `TEAMS_COOKIE`
