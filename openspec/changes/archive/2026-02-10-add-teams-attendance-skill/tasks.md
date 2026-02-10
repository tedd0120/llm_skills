# 任务清单

## 前置任务
- [x] 1. 在 `.env.example` 添加 `TEAMS_EM_CODE` 和 `TEAMS_AUTHORIZATION` 模板

## 核心实现
- [x] 2. 创建 `.agent/skills/teams-attendance/scripts/fetch_attendance.py`
  - 从 `.env` 加载敏感配置
  - 保留原有业务逻辑
  - 提供 CLI 入口

- [x] 3. 创建 `.agent/skills/teams-attendance/SKILL.md`
  - 描述功能用途
  - 提供使用示例
  - 说明参数和输出格式

## 清理
- [x] 4. 删除 `teams工时.py` 原文件

## 验证
- [x] 5. 配置 `.env` 并运行脚本验证功能


