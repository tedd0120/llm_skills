# 变更：姓名搜索自动聚焦与同名结果切换

## 为什么
当前组织树搜索仅执行高亮和祖先展开，不会自动把目标节点移动到视图中心。数据量较大时，用户需要手动拖拽寻找命中节点，效率低。

同时，当存在多个同名成员时，缺少结果切换入口，无法在同名节点间快速定位。

## 变更内容
- 姓名搜索命中后，画布自动跳转并以命中节点为中心。
- 搜索框旁新增 `pre` / `next` 按钮，用于在多个同名命中节点之间切换中心定位。
- 结果选择规则：优先“姓名精确匹配”；若无精确匹配，则回退为“姓名包含匹配”。
- 验证用例统一使用 `.env` 中全量 `TEAMS_GROUP_CODES` 的批量抓取结果，不再使用单群样例。

## 影响
- 受影响规范：`group-members-org-tree-skill`
- 受影响代码：
  - `.agent/skills/teams-group-members/scripts/generate_org_tree_html.py`
  - `.agent/skills/teams-group-members/SKILL.md`

## 依赖关系
- 建议在 `update-org-tree-ios-compact-interaction` 应用后实施，本变更基于其现有搜索与画布交互能力增量扩展。
