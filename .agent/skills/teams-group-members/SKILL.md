---
description: 获取360Teams群组成员列表并解析详细信息
---

# Teams群组成员查询 Skill

根据群组代码从360teams平台获取群组成员列表，解析并返回每个成员的详细组织架构信息。

## 前置配置

在项目根目录 `.env` 文件中配置：

```env
TEAMS_AUTHORIZATION=你的授权令牌
```

## 功能

1. **成员列表获取** - 根据群组代码调用 API 获取所有成员
2. **信息解析** - 自动解析 `extra` 嵌套 JSON，扁平化输出
3. **CLI支持** - 命令行直接查询

## 使用方法

### 命令行调用

```bash
# 查询指定群组
python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o
```

### 代码调用

```python
from scripts.fetch_group_members import fetch_group_members

# 获取群组成员
members = fetch_group_members("FhSnheH3T_grT5yzxqVS5o")

for m in members:
    print(f"{m['name']} - {m['deptName']} - 上级: {m['superior']}")
```

## 参数说明

| 参数 | 类型 | 说明 |
|-----|------|-----|
| group_code | str | 群组代码（必填） |
| authorization | str | 授权令牌（可选，默认从 .env 读取） |
| verbose | bool | 是否打印成员列表，默认 True |

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
