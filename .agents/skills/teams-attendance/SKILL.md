---
name: teams-attendance
description: 获取360teams考勤数据并计算工时统计
---

# Teams 考勤数据 Skill

从 360teams 平台获取员工考勤数据，计算有效工作日、平均工时及目标达标预测，并输出结构化统计回复。

## 前置配置

在项目根目录 `.env` 文件中配置：

```env
TEAMS_EM_CODE=你的员工编码
TEAMS_AUTHORIZATION=你的授权令牌
```

## 功能

1. **考勤数据获取**：调用 API 获取指定月份考勤打卡明细。
2. **工时统计与预测**：自动计算累计工时、日均工时，并预测剩余工作日达标所需工时。
3. **CSV 导出**：自动保存考勤明细（默认落盘至 `data/attendance_YYYYMM.csv`）。

---

## 使用方法

```bash
# 查询当前月份
python .agents/skills/teams-attendance/scripts/fetch_attendance.py

# 查询指定月份
python .agents/skills/teams-attendance/scripts/fetch_attendance.py --month 2026-01

# 导出 CSV 到指定路径
python .agents/skills/teams-attendance/scripts/fetch_attendance.py --month 2026-01 --output ./data/attendance_202601.csv
```

### 参数说明

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `--month` | str | 查询月份，格式 `YYYY-MM`；不传则默认查询当前自然月 |
| `--output` | str | CSV 输出路径，默认 `data/attendance_YYYYMM.csv` |

---

## 执行流程

1. **运行脚本**：执行上方命令获取实时考勤数据（必须运行脚本获取实时真实数据，禁止估算）。
2. **解析输出**：提取统计数值、工时指标与明细列表。
3. **格式化呈现**：查阅 **[references/reply-template.md](references/reply-template.md)**，按结构化模板与过滤规则向用户回复。
