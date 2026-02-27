# 变更：收紧组织树布局并升级为 iOS 极简交互

## 为什么
当前 `teams-group-members` 生成的组织树页面存在以下问题：
- 横向布局过宽，层级稍深时需要频繁拖拽才能浏览。
- 节点缺少悬停信息辅助，无法快速查看“当前节点到根节点”的上游链路。
- 画布拖动与文本选择冲突，用户在节点上无法稳定进行鼠标框选文本。
- 视觉风格偏工程化，缺少统一的 iOS 极简风格与字体体系。

## 变更内容
- 调整组织树节点尺寸与层级间距，使默认布局更紧凑。
- 新增节点悬停 1 秒提示：显示当前节点上游祖先链（根 -> ... -> 父级），格式为“姓名-部门”。
- 调整交互优先级：节点文本可被鼠标选择，且文本选择不触发画布拖动。
- 更新页面视觉为 iOS 极简风格（色彩、圆角、阴影、字体栈）。

## 影响
- 受影响规范：`group-members-org-tree-skill`
- 受影响代码：
  - `.agent/skills/teams-group-members/scripts/generate_org_tree_html.py`
  - `.agent/skills/teams-group-members/SKILL.md`

## 依赖关系
- 建议在 `update-group-members-auto-html` 应用后实施本变更，以保证最新 HTML 由抓取流程统一产出。
