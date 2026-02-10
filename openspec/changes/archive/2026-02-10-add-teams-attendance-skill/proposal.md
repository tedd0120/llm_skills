# 将 teams工时.py 固化为 Skill

## 背景

当前 `teams工时.py` 脚本可以从 360teams 平台获取考勤数据并计算工时统计，但存在以下问题：
- `emCode` 和 `Authorization` 敏感信息硬编码在代码中
- 未遵循项目 Skill 结构规范

本提案将该脚本重构为标准 Skill，敏感配置通过 `.env` 文件加载。

## 变更范围

### 新增

1. **Skill 目录结构**
   - `.agent/skills/teams-attendance/SKILL.md` - Skill 文档
   - `.agent/skills/teams-attendance/scripts/fetch_attendance.py` - 核心脚本

2. **环境变量配置**
   - 在 `.env.example` 中添加模板配置项

### 删除

- `teams工时.py` - 原脚本将被 Skill 替代

## 用户确认事项

> [!IMPORTANT]
> 请确认以下环境变量命名是否符合您的偏好：
> - `TEAMS_EM_CODE` - 员工编码
> - `TEAMS_AUTHORIZATION` - 360teams 授权令牌

## 验证计划

### 手动验证
1. 在 `.env` 中配置 `TEAMS_EM_CODE` 和 `TEAMS_AUTHORIZATION`
2. 运行 `python .agent/skills/teams-attendance/scripts/fetch_attendance.py`
3. 确认输出与原脚本一致
