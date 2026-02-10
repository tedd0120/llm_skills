# 功能：group-members-skill

## 新增需求

### 需求：从环境变量加载敏感配置

脚本启动时**必须**从 `.env` 文件加载 `TEAMS_AUTHORIZATION` 和 `TEAMS_COOKIE`，**禁止**在代码中硬编码敏感信息。

#### 场景：环境变量已配置
- 当用户已在 `.env` 配置有效凭据时
- 脚本**必须**正常执行并返回群组成员数据

#### 场景：环境变量缺失
- 当 `.env` 中缺少必需配置时
- 脚本**必须**抛出明确错误提示，指明缺少哪些变量

---

### 需求：获取并解析群组成员信息

**必须**提供 `fetch_group_members(group_code)` 函数，根据群组代码调用 API 并返回解析后的成员列表。

每个成员记录**必须**包含以下字段：
- `name` - 姓名
- `id` - 员工工号
- `userName` - 登录账号
- `role` - 角色（1=群主, 4=普通成员）
- `deptName` - 部门名称
- `deptCode` - 部门编码
- `superior` - 直属上级
- `bpName` - 对应BP
- `workPlaceName` - 办公地点
- `sex` - 性别（0=男, 1=女）
- `portrait_url` - 头像链接
- `create_dt` - 加入时间

#### 场景：获取有效群组的成员
- 调用 `fetch_group_members("FhSnheH3T_grT5yzxqVS5o")`
- **必须**返回包含所有成员详细信息的字典列表
- `extra` 字段中的嵌套 JSON **必须**被解析并扁平化到成员记录中

#### 场景：群组代码无效
- 当传入无效的群组代码时
- **必须**返回空列表并打印错误提示

---

### 需求：CLI 入口支持

脚本**必须**可通过命令行直接运行，**必须**支持 `--group` 参数指定群组代码。

#### 场景：命令行调用
- 运行 `python fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o`
- **必须**输出格式化的成员列表到控制台
