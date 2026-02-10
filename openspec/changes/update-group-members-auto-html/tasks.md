## 1. 实施
- [x] 1.1 更新 `fetch_group_members.py`：单群/批量抓取完成后默认生成 HTML
- [x] 1.2 调整 HTML 生成脚本为内部能力，移除独立 CLI 入口
- [x] 1.3 确保批量抓取过程中不会为中间单群结果重复生成 HTML，仅对最终结果生成

## 2. 文档
- [x] 2.1 更新 `.agent/skills/teams-group-members/SKILL.md`，移除单独生成 HTML 的用法与接口说明

## 3. 验证
- [x] 3.1 语法校验：`python -m py_compile .agent/skills/teams-group-members/scripts/fetch_group_members.py`
- [x] 3.2 语法校验：`python -m py_compile .agent/skills/teams-group-members/scripts/generate_org_tree_html.py`
- [x] 3.3 OpenSpec 校验：`openspec-cn validate update-group-members-auto-html --strict`
