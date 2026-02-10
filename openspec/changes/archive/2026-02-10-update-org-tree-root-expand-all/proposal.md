# 变更：调整组织树根节点语义与展开交互

## 为什么

当前组织树已按 `superior` 构建，但页面交互不满足期望的“以无上级人员作为根节点，并可点开根节点仅展开一层下级”的浏览方式。需要补充明确规则，避免展示结果与用户心智不一致。

## 变更内容

- 明确根节点定义：`superior` 为空（或无法匹配上级）的成员作为根节点。
- 明确根节点数量：保留多个根节点，不强制合并为单一虚拟根。
- 新增交互要求：点击任一根节点时，仅展开该根节点的一层下级，孙辈及更深层保持折叠。
- 保持与抓取 Skill 解耦，仅调整 `teams-org-tree-html` 的展示与交互行为。

## 影响

- 受影响规范：`group-members-org-tree-skill`
- 受影响代码（实施阶段）：
  - `.agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`
  - `.agent/skills/teams-org-tree-html/SKILL.md`
