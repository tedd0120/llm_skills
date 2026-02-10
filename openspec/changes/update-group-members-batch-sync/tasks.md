# 任务列表

## 1. 脚本能力增强

- [x] 1.1 在 `fetch_group_members.py` 增加保存路径参数（函数入参 + CLI 参数）
- [x] 1.2 增加从 `.env` 读取 `TEAMS_GROUP_CODES` 的解析逻辑
- [x] 1.3 增加批量抓取并集去重逻辑（按 `id` 去重，`id` 为空回退 `userName`）
- [x] 1.4 实现统一写入 JSON 文件（自动创建目录）

## 2. 文档与配置更新

- [x] 2.1 更新 `.agent/skills/teams-group-members/SKILL.md`，补充批量模式与保存路径用法
- [x] 2.2 更新 `.env.example`，新增 `TEAMS_GROUP_CODES` 示例

## 3. 验证

- [x] 3.1 语法校验：`python -m py_compile .agent/skills/teams-group-members/scripts/fetch_group_members.py`
- [x] 3.2 单群模式验证：`python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group <group_code> --output data/single.json`
- [x] 3.3 批量模式验证：配置 `TEAMS_GROUP_CODES` 后运行 `python .agent/skills/teams-group-members/scripts/fetch_group_members.py --output data/all_groups.json`
