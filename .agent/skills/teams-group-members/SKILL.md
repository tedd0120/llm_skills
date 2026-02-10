---
description: 获取360Teams群组成员并生成组织架构树HTML，支持多群并集去重与结果落盘
---

# Teams 群组成员与组织树 Skill

统一完成两类任务：
1. 从 360Teams 抓取群组成员并输出标准 JSON
2. 基于成员 JSON 生成可离线打开的组织架构树 HTML

`teams-org-tree-html` 的能力已合并到本 Skill。

## 前置配置

在项目根目录 `.env` 文件中配置：

```env
TEAMS_AUTHORIZATION=你的授权令牌
TEAMS_GROUP_CODES=群组A,群组B,群组C
```

## 功能

1. 成员列表获取：根据群组代码调用 API 获取所有成员
2. 信息解析：自动解析 `extra` 嵌套 JSON，扁平化输出
3. 批量并集去重：按固定群组列表聚合成员并去重（优先 `id`，回退 `userName`）
4. 虚拟上级补齐：若成员 `superior` 不在当前列表中，自动创建同名虚拟上级节点（同名合并）
5. 结果落盘：支持通过参数指定保存路径（JSON）
6. 组织树可视化：将 JSON 转为离线单文件 HTML（支持缩放、拖拽、搜索与高亮）

## 使用方法

### 命令行调用

```bash
# 1) 查询指定群组并保存 JSON
python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o --output data/single_group_members.json

# 2) 按 .env 中 TEAMS_GROUP_CODES 批量抓取并保存 JSON
python .agent/skills/teams-group-members/scripts/fetch_group_members.py --output data/all_groups_members.json

# 3) 从成员 JSON 生成组织树 HTML
python .agent/skills/teams-group-members/scripts/generate_org_tree_html.py --input data/all_groups_members.json --output data/all_groups_org_tree.html

# 4) 指定抓取时间（可选）
python .agent/skills/teams-group-members/scripts/generate_org_tree_html.py --input data/all_groups_members.json --output data/all_groups_org_tree.html --fetched-date "2026-02-10 18:30:00"
```

### 代码调用

```python
from scripts.fetch_group_members import fetch_group_members, fetch_group_members_union
from scripts.generate_org_tree_html import generate_org_tree_html

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

# 3) 组织树 HTML 生成
generate_org_tree_html(
    input_path="data/all_groups_members.json",
    output_path="data/all_groups_org_tree.html",
)
```

## 参数说明

### `fetch_group_members(group_code, authorization=None, verbose=True, save_path=None, fill_virtual_superiors=True)`

| 参数 | 类型 | 说明 |
|---|---|---|
| group_code | str | 群组代码（必填） |
| authorization | str | 授权令牌（可选，默认从 `.env` 读取） |
| verbose | bool | 是否打印成员列表，默认 `True` |
| save_path | str | 结果保存路径（可选，JSON） |
| fill_virtual_superiors | bool | 是否补齐虚拟上级节点，默认 `True` |

### `fetch_group_members_union(group_codes, authorization=None, verbose=True, save_path=None)`

| 参数 | 类型 | 说明 |
|---|---|---|
| group_codes | list[str] | 群组代码列表（必填） |
| authorization | str | 授权令牌（可选，默认从 `.env` 读取） |
| verbose | bool | 是否打印抓取进度，默认 `True` |
| save_path | str | 聚合结果保存路径（可选，JSON） |

### `generate_org_tree_html(input_path, output_path, fetched_date="")`

| 参数 | 类型 | 说明 |
|---|---|---|
| input_path | str | 输入成员 JSON 文件路径（必填） |
| output_path | str | 输出 HTML 文件路径（必填） |
| fetched_date | str | 抓取日期（可选，未传时使用输入文件最后修改时间） |

## 输出格式

成员抓取返回 `list[dict]`，每个字典包含以下字段：

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

HTML 页面特性：
1. 首屏显示根节点，根节点横向排布
2. 点击节点展开或收起直属下级
3. 支持滚轮缩放、拖动画布、关键字搜索与命中高亮
