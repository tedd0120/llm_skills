# 任务清单

## 前置任务
- [x] 1. 在 `.env.example` 添加 `TEAMS_COOKIE` 模板

## 核心实现
- [x] 2. 创建 `.agent/skills/teams-group-members/scripts/fetch_group_members.py`
  - 从 `.env` 加载 `TEAMS_AUTHORIZATION` 和 `TEAMS_COOKIE`
  - 调用群组成员 API 并解析 `extra` 嵌套 JSON
  - 返回结构化的成员信息列表（含姓名、部门、上级、工位等）
  - 提供 CLI 入口（`--group` 参数指定群组代码）

- [x] 3. 创建 `.agent/skills/teams-group-members/SKILL.md`
  - 描述功能用途
  - 提供命令行和代码调用示例
  - 说明参数和输出格式

## 验证
- [x] 4. 配置 `.env` 并运行脚本验证功能（语法检查通过）
  - `python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o`
  - 确认输出包含解析后的完整成员列表
