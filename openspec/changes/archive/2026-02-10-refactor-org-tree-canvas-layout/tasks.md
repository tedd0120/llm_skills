# 任务列表

## 1. 布局与交互

- [x] 1.1 将 HTML 渲染改为 SVG 画布（节点 + 连线）
- [x] 1.2 实现首屏仅显示根节点并横向排布
- [x] 1.3 实现点击节点展开/收起直属下级
- [x] 1.4 实现画布拖动与缩放

## 2. 保留能力

- [x] 2.1 保留头部信息：抓取日期、总人数
- [x] 2.2 保留搜索/高亮，并支持自动展开命中祖先路径
- [x] 2.3 更新 `.agent/skills/teams-org-tree-html/SKILL.md` 说明新布局与交互

## 3. 验证

- [x] 3.1 语法校验：`python -m py_compile .agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`
- [x] 3.2 端到端验证：生成 HTML 后确认根节点横排、点击展开下级、可拖拽缩放
