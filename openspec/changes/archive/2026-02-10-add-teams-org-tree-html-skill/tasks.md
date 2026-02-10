# 任务列表

## 1. 新增独立 Skill

- [x] 1.1 创建 `.agent/skills/teams-org-tree-html/SKILL.md`，说明与抓取 Skill 的职责分离
- [x] 1.2 创建 `.agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`

## 2. 组织树与页面能力

- [x] 2.1 实现从 JSON 列表读取成员并按 `superior` 构建树
- [x] 2.2 生成离线 HTML 树状页面（可折叠展示）
- [x] 2.3 实现前端简单搜索与高亮（姓名/工号/部门）
- [x] 2.4 在页面头部展示“数据抓取日期”和“总人数”

## 3. CLI 与验证

- [x] 3.1 提供输入文件与输出文件参数（如 `--input`、`--output`）
- [x] 3.2 提供可选抓取日期参数（如 `--fetched-date`，未传时回退文件修改时间）
- [x] 3.3 语法校验：`python -m py_compile .agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`
- [x] 3.4 使用已有 JSON 进行端到端验证，输出 HTML 可本地打开并完成搜索高亮
