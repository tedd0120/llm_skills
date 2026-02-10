# 任务列表

- [ ] 1. 修改 `fetch_group_members.py`：移除 `TEAMS_COOKIE` 相关代码
  - 移除 `TEAMS_COOKIE` 环境变量加载和检查
  - 移除 `cookie` 函数参数
  - 移除请求 headers 中的 `Cookie` 字段
  - 验证：`python -m py_compile .agent/skills/teams-group-members/scripts/fetch_group_members.py`

- [ ] 2. 更新 `SKILL.md`：移除 `TEAMS_COOKIE` 配置和参数说明
  - 验证：检查文档中不再包含 `TEAMS_COOKIE` 或 `cookie` 参数

- [ ] 3. 更新 `.env.example`：移除 `TEAMS_COOKIE` 模板行
  - 验证：确认文件内容正确

- [ ] 4. 端到端验证：运行脚本确认功能正常
  - `python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o`
  - 确认输出 28 名成员
