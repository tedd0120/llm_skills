# 精简 teams-group-members 环境变量配置

## 背景

`teams-group-members` Skill 的 `fetch_group_members.py` 脚本当前要求配置两个环境变量：
- `TEAMS_AUTHORIZATION`：授权令牌
- `TEAMS_COOKIE`：请求Cookie（含 `RCESESSIONID` 和 `username`）

通过实际 API 测试发现，**`TEAMS_COOKIE` 是完全多余的**——仅使用 `TEAMS_AUTHORIZATION` 即可成功获取群组成员数据。

### 测试结果

| 测试组合 | HTTP Status | API code | 成员数量 | 结论 |
|---------|-------------|----------|---------|------|
| Authorization + Cookie | 200 | 0 (成功) | 28 | ✅ 基线正常 |
| **仅 Authorization** | **200** | **0 (成功)** | **28** | **✅ Cookie 不需要** |
| 仅 Cookie | 200 | 10301 (缺少认证参数) | 0 | ❌ |
| 都不传 | 200 | 10301 (缺少认证参数) | 0 | ❌ |

## 变更范围

### 修改

1. **`fetch_group_members.py`** - 移除 `TEAMS_COOKIE` 相关逻辑
   - 移除 `TEAMS_COOKIE` 环境变量加载
   - 移除 `cookie` 函数参数
   - 移除请求 headers 中的 `Cookie` 字段
   - 简化 `_check_env()` 检查

2. **`SKILL.md`** - 更新文档
   - 移除 `TEAMS_COOKIE` 配置说明
   - 移除 `cookie` 参数说明

3. **`.env.example`** - 移除 `TEAMS_COOKIE` 模板行

4. **`.env`** - 移除 `TEAMS_COOKIE` 行（用户可手动删除）

## 验证计划

### 自动验证
1. 运行 `python .agent/skills/teams-group-members/scripts/fetch_group_members.py --group FhSnheH3T_grT5yzxqVS5o`
2. 确认输出包含完整的 28 名成员列表
3. 运行 `python -m py_compile .agent/skills/teams-group-members/scripts/fetch_group_members.py`
