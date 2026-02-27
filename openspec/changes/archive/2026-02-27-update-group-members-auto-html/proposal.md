# 变更：teams-group-members 抓取默认生成 HTML 并移除独立入口

## 为什么
当前 `teams-group-members` 需要先抓取成员 JSON，再手动调用独立 `generate_org_tree_html.py` 才能得到组织树 HTML。这个流程多一步且容易遗漏，不符合“抓取后立即得到最新可视化结果”的使用习惯。

## 变更内容
- 调整抓取流程：单群与批量抓取完成后，默认基于本次最新数据生成一份组织树 HTML。
- 移除单独生成 HTML 的公开接口（独立 CLI 入口），统一由抓取入口触发。
- 更新 Skill 文档与示例，删除“先抓取再单独生成 HTML”的说明。

## 影响
- 受影响规范：`group-members-skill`、`group-members-org-tree-skill`
- 受影响代码：
  - `.agent/skills/teams-group-members/scripts/fetch_group_members.py`
  - `.agent/skills/teams-group-members/scripts/generate_org_tree_html.py`
  - `.agent/skills/teams-group-members/SKILL.md`
