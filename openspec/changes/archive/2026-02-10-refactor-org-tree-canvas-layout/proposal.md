# 变更：将组织架构页改为画布式决策树布局

## 为什么

现有页面是列表/折叠树样式，不能满足“根节点横向排布 + 点击后向下展开 + 画布拖动缩放”的决策树浏览体验。

## 变更内容

- 将 `teams-org-tree-html` 渲染从列表树改为画布式树图（SVG）。
- 首屏仅显示根节点（`superior` 为空或无法匹配上级）并横向排布。
- 点击某个节点后，在其下方显示直属下级（逐层展开）。
- 支持画布拖动（pan）和缩放（zoom）。
- 保留搜索/高亮能力，并保留“数据抓取日期、总人数”头部信息。

## 影响

- 受影响规范：`group-members-org-tree-skill`
- 受影响代码（实施阶段）：
  - `.agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`
  - `.agent/skills/teams-org-tree-html/SKILL.md`
