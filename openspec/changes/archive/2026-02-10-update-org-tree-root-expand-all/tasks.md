# 任务列表

## 1. 根节点规则与交互实现

- [x] 1.1 调整 `generate_org_tree_html.py`，明确并保留多个根节点展示
- [x] 1.2 新增根节点点击后“仅展开一层下级”逻辑
- [x] 1.3 保持非根节点现有展开行为不变

## 2. 文档更新

- [x] 2.1 更新 `.agent/skills/teams-org-tree-html/SKILL.md`，补充“多根节点 + 根节点仅展开一层下级”说明

## 3. 验证

- [x] 3.1 语法校验：`python -m py_compile .agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`
- [x] 3.2 端到端验证：用现有 JSON 生成 HTML，确认存在多个根节点且点击根节点仅展开一层下级
