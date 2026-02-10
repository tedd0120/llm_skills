## 1. 实施
- [x] 1.1 在组织树工具栏新增 `pre` / `next` 按钮，并绑定搜索结果切换事件
- [x] 1.2 增加姓名搜索命中集合与活动索引管理（精确匹配优先，回退包含匹配）
- [x] 1.3 实现命中节点自动居中逻辑（首次搜索与 pre/next 切换均触发）
- [x] 1.4 保持现有搜索高亮与祖先展开逻辑，避免行为回归

## 2. 文档
- [x] 2.1 更新 `.agent/skills/teams-group-members/SKILL.md`，补充“姓名搜索自动居中 + pre/next 同名切换”说明

## 3. 验证
- [x] 3.1 语法校验：`python -m py_compile .agent/skills/teams-group-members/scripts/generate_org_tree_html.py`
- [x] 3.2 全量群组冒烟：`python .agent/skills/teams-group-members/scripts/fetch_group_members.py --output data/full_groups_search_focus_members.json`
- [x] 3.3 产物检查：确认 `data/full_groups_search_focus_members_org_tree.html` 包含 `pre` / `next` 控件与搜索自动居中逻辑标识
- [x] 3.4 OpenSpec 校验：`openspec-cn validate update-org-tree-search-focus-navigation --strict`
