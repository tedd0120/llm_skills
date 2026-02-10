# 变更：增强 teams-group-members 的批量同步与保存路径能力

## 为什么

当前 `teams-group-members` 仅支持按单个群组抓取并在终端输出，无法通过统一入口把多群成员数据聚合后持久化到指定位置。实际使用中，人员信息分散在多个固定群组，需要每次抓取时按固定列表统一更新，并得到去重后的完整成员集合。

## 变更内容

- 新增保存路径入参，允许调用方指定结果写入位置。
- 新增从 `.env` 读取固定群组列表的能力，用于批量抓取。
- 新增批量聚合逻辑：按群组列表抓取成员后做并集去重，输出统一结果。
- 调整 CLI 行为，支持“单群抓取”与“按 `.env` 列表批量同步”两种模式。
- 更新 `SKILL.md` 与 `.env.example`，补充新参数和环境变量说明。

## 影响

- 受影响规范：`group-members-skill`
- 受影响代码：
  - `.agent/skills/teams-group-members/scripts/fetch_group_members.py`
  - `.agent/skills/teams-group-members/SKILL.md`
  - `.env.example`
