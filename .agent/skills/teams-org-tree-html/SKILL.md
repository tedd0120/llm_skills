---
description: 从已有成员JSON生成可拖拽缩放的决策树HTML（支持搜索/高亮）
---

# Teams 组织架构树 HTML Skill

将已抓取的成员 JSON 列表转换为可本地打开的 HTML 决策树页面（画布式布局）。

该 Skill 与 `teams-group-members` 抓取 Skill 职责分离：
- `teams-group-members` 负责抓取并保存成员 JSON
- `teams-org-tree-html` 负责读取 JSON 并生成可视化 HTML

## 输入数据要求

输入文件必须是 `list[dict]`，并包含以下关键字段（来自抓取结果）：
- `name`
- `id`
- `deptName`
- `superior`

组织关系按 `superior -> name` 建树。

## 功能

1. 读取本地 JSON 成员列表
2. 按 `superior` 构建树状组织结构
3. 首屏仅显示根节点，根节点横向排布
4. 点击节点展开/收起直属下级
5. 生成离线单文件 HTML（无需外部依赖）
6. 页面支持画布拖动与滚轮缩放
7. 页面支持简单搜索和命中高亮（姓名/工号/部门）
8. 页面展示“数据抓取日期”和“总人数”

## 使用方法

```bash
python .agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py \
  --input data/all_groups_union_test.json \
  --output data/all_groups_org_tree.html
```

可选传入抓取日期：

```bash
python .agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py \
  --input data/all_groups_union_test.json \
  --output data/all_groups_org_tree.html \
  --fetched-date "2026-02-10 18:30:00"
```

## 参数说明

| 参数 | 类型 | 说明 |
|---|---|---|
| `--input` | str | 输入成员 JSON 文件路径（必填） |
| `--output` | str | 输出 HTML 文件路径（必填） |
| `--fetched-date` | str | 抓取日期（可选），未传时使用输入文件最后修改时间 |

## 限制说明

- 若同名人员同时存在，`superior` 到 `name` 的匹配会按首次匹配处理。
- 搜索命中会自动展开命中节点的祖先路径。
