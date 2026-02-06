---
description: 获取360teams考勤数据并计算工时统计
---

# Teams考勤数据 Skill

从360teams平台获取员工考勤数据，计算有效工作日和平均工时。

## 前置配置

在项目根目录 `.env` 文件中配置：

```env
TEAMS_EM_CODE=你的员工编码
TEAMS_AUTHORIZATION=你的授权令牌
```

## 功能

1. **考勤数据获取** - 从360teams API获取指定月份考勤明细
2. **工时计算** - 自动计算有效工作日、总工时、平均工时
3. **CLI支持** - 命令行直接查询
4. **CSV导出** - 可选导出考勤明细到CSV文件

## 使用方法

### 命令行调用

```bash
# 查询当前月份
python .agent/skills/teams-attendance/scripts/fetch_attendance.py

# 查询指定月份
python .agent/skills/teams-attendance/scripts/fetch_attendance.py --month 2026-01

# 导出CSV到指定路径
python .agent/skills/teams-attendance/scripts/fetch_attendance.py --month 2026-01 --output ./data/attendance_202601.csv
```

### 代码调用

```python
from scripts.fetch_attendance import parsed_att_date

# 获取2026年1月考勤统计
avg_hours, att_df = parsed_att_date("2026-01")

# 获取并导出到CSV
avg_hours, att_df = parsed_att_date("2026-01", output_path="./data/att.csv")

print(f"平均工时: {avg_hours}")
print(att_df)
```

## 参数说明

| 参数 | 类型 | 说明 |
|-----|------|-----|
| check_month | str | 查询月份，格式 YYYY-MM |
| verbose | bool | 是否打印统计信息，默认 True |
| output_path | str | CSV输出路径（可选） |

## 输出格式

DataFrame 包含以下列：

| 列名 | 说明 |
|-----|------|
| 日期 | 考勤日期 |
| 月份 | 所属月份 |
| 假期flag | 是否假期 (0=工作日) |
| 上班打卡 | 上班打卡时间 |
| 下班打卡 | 下班打卡时间 |
| 备注 | 考勤状态 (迟到/早退/年假等) |
| 工时 | 当日工时 (小时) |
| 有效工作日 | 0/0.5/1 |
