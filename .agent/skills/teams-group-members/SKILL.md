---
description: 获取360Teams群组成员列表，支持多群并集去重与结果落盘
---

# Teams群组成员查询 Skill

根据群组代码从360teams平台获取群组成员列表，解析并返回每个成员的详细组织架构信息。支持按 `.env` 中固定群组列表批量抓取，并对结果做并集去重。

## 前置配置

在项目根目录 `.env` 文件中配置：

```env
TEAMS_AUTHORIZATION=你的授权令牌
TEAMS_GROUP_CODES=群组A,群组B,群组C
```

## 功能

1. **成员列表获取** - 根据群组代码调用 API 获取所有成员
2. **信息解析** - 自动解析 `extra` 嵌套 JSON，扁平化输出
3. **批量并集去重** - 按固定群组列表聚合成员并去重（优先 `id`，回退 `userName`）
4. **虚拟上级补齐** - 若成员 `superior` 不在当前列表中，自动创建同名虚拟上级节点（同名合并）
5. **结果落盘** - 支持通过参数指定保存路径（JSON）
6. **CLI支持** - 命令行支持单群和批量两种模式

## 使用方法

### 命令行调用

```bash
# 1) 查询指定群组并保存
python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o --output data/single_group_members.json

# 2) 按 .env 中 TEAMS_GROUP_CODES 批量抓取并保存
python .agent/skills/teams-group-members/scripts/fetch_group_members.py --output data/all_groups_members.json
```

### 代码调用

```python
from scripts.fetch_group_members import fetch_group_members, fetch_group_members_union

# 1) 单群抓取
single_members = fetch_group_members(
    "FhSnheH3T_grT5yzxqVS5o",
    save_path="data/single_group_members.json"
)

# 2) 多群抓取并集去重
union_members = fetch_group_members_union(
    ["oMNKGFroR6YjsKVGNkgCCk", "qY1ZR8mGQ2oqs6hG7KlCA0"],
    save_path="data/all_groups_members.json"
)

for m in union_members:
    print(f"{m['name']} - {m['deptName']} - 上级: {m['superior']}")
```

## 参数说明

### `fetch_group_members(group_code, authorization=None, verbose=True, save_path=None)`

| 参数 | 类型 | 说明 |
|---|---|---|
| group_code | str | 群组代码（必填） |
| authorization | str | 授权令牌（可选，默认从 `.env` 读取） |
| verbose | bool | 是否打印成员列表，默认 `True` |
| save_path | str | 结果保存路径（可选，JSON） |

### `fetch_group_members_union(group_codes, authorization=None, verbose=True, save_path=None)`

| 参数 | 类型 | 说明 |
|---|---|---|
| group_codes | list[str] | 群组代码列表（必填） |
| authorization | str | 授权令牌（可选，默认从 `.env` 读取） |
| verbose | bool | 是否打印抓取进度，默认 `True` |
| save_path | str | 聚合结果保存路径（可选，JSON） |

## 输出格式

返回 `list[dict]`，每个字典包含以下字段：

| 字段 | 类型 | 说明 |
|-----|------|-----|
| name | str | 姓名 |
| id | str | 员工工号 |
| userName | str | 登录账号 |
| role | int | 角色编码（1=群主, 4=普通成员） |
| role_desc | str | 角色描述 |
| deptName | str | 部门名称 |
| deptCode | str | 部门编码 |
| superior | str | 直属上级 |
| bpName | str | 对应BP |
| workPlaceName | str | 办公地点 |
| workPlaceCode | str | 办公地点编码 |
| sex | int | 性别编码（0=男, 1=女） |
| sex_desc | str | 性别描述 |
| portrait_url | str | 头像链接 |
| create_dt | int | 加入群组时间戳（毫秒） |
| gorder | int | 群组内排序 |
| is_virtual | bool | 是否虚拟上级节点（仅补齐节点为 `true`） |
