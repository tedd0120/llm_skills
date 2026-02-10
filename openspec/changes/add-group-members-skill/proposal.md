# 新增360Teams群组成员查询 Skill

## 背景

360Teams 提供群组成员列表 API（`/api/qfin-api/rce-app/app/groups/members/{groupCode}`），可返回群组内所有成员的详细信息，包括姓名、部门、上级、工位等组织架构数据。

本提案将该 API 封装为标准 Skill，方便 AI 助手根据群组代码查询并解析群组成员信息。

## 变更范围

### 新增

1. **Skill 目录结构**
   - `.agent/skills/teams-group-members/SKILL.md` - Skill 文档
   - `.agent/skills/teams-group-members/scripts/fetch_group_members.py` - 核心脚本

2. **环境变量**
   - 复用已有的 `TEAMS_AUTHORIZATION`（与 teams-attendance 共享）

### 修改

- `.env.example` - 添加 `TEAMS_COOKIE` 模板（API 需要 cookie 中的 `RCESESSIONID`）

## 用户确认事项

> [!IMPORTANT]
> 1. API 请求需要 `authorization` 和 `cookie`（含 `RCESESSIONID`）。`TEAMS_AUTHORIZATION` 已在 `.env.example` 中定义，是否需要新增 `TEAMS_COOKIE` 环境变量？还是 cookie 可以从现有配置中推导？
> 2. `response.txt` 中的 `extra` 字段是嵌套 JSON 字符串，计划将其解析为扁平化的字典。请确认所需字段。

## 验证计划

### 手动验证
1. 在 `.env` 中配置 `TEAMS_AUTHORIZATION` 和 `TEAMS_COOKIE`
2. 运行 `python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o`
3. 确认输出包含完整的成员列表及各字段
