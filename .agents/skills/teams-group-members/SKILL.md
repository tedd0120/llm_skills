---
name: teams-group-members
description: 获取360Teams群组成员并生成组织架构树HTML，支持多群并集去重与结果落盘
---

# Teams 群组成员与组织树 Skill

统一完成两类任务：
1. 从 360Teams 抓取群组成员并输出标准 JSON 数据；
2. 自动生成可离线打开的单文件交互式组织架构树 HTML。

## 前置配置

在项目根目录 `.env` 文件中配置：

```env
TEAMS_AUTHORIZATION=你的授权令牌
TEAMS_GROUP_CODES=群组A,群组B,群组C
```

## 功能特性

1. **成员列表获取与扁平化**：提取嵌套属性，统一字段口径。
2. **多群并集去重**：支持跨多个群组聚合成员并按工号去重。
3. **虚拟上级补齐**：自动补齐不在群内的上级节点，维系完整树结构。
4. **可视化组织树生成**：自动产出分栏钻取、带路径导航与全局搜索的离线 HTML。

---

## 使用方法（CLI）

```bash
# 1) 查询指定单群并落盘
python .agents/skills/teams-group-members/scripts/fetch_group_members.py \
  --group FhSnheH3T_grT5yzxqVS5o \
  --output data/single_group_members.json

# 2) 按 .env 中 TEAMS_GROUP_CODES 批量抓取多群并集去重
python .agents/skills/teams-group-members/scripts/fetch_group_members.py \
  --output data/all_groups_members.json
```

**产物说明**：
- 传入 `--output data/xxx.json` 时，同步生成 `data/xxx_org_tree.html`；
- 未指定 `--output` 时，默认输出 `data/latest_group_members_org_tree.html`。

*注：Python SDK 函数签名、返回值字段与 HTML 交互详情见 [references/api-reference.md](references/api-reference.md)。*
