# 变更：新增 Teams 成员组织架构 HTML 生成 Skill

## 为什么

当前 `teams-group-members` 已能抓取并落盘成员 JSON，但缺少可视化能力。用户需要把已有成员列表解析为组织架构树状图，并以 HTML 形式展示，且要求与“抓取”能力解耦，形成独立 Skill。

## 变更内容

- 新增独立 Skill（建议目录：`.agent/skills/teams-org-tree-html/`），仅负责读取成员 JSON 并生成 HTML。
- 组织树父子关系以成员字段 `superior` 为准构建。
- HTML 页面支持简单搜索与高亮匹配结果。
- HTML 页面展示“数据抓取日期”和“总人数”。
- 与 `teams-group-members` 抓取 Skill 保持职责分离：抓取负责产出 JSON，HTML Skill 负责可视化，不引入网络请求依赖。

## 影响

- 受影响规范：`group-members-org-tree-skill`（新增）
- 受影响代码（实施阶段）：
  - `.agent/skills/teams-org-tree-html/SKILL.md`（新增）
  - `.agent/skills/teams-org-tree-html/scripts/generate_org_tree_html.py`（新增）
