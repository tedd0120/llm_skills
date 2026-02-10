# 为 teams-attendance skill 添加 CSV 导出功能

## 背景

当前 `fetch_attendance.py` 脚本可以获取考勤数据并打印统计信息，但无法将明细数据持久化。用户希望能够将考勤明细导出为 CSV 文件。

## 变更范围

### 修改

1. **`.agent/skills/teams-attendance/scripts/fetch_attendance.py`**
   - `parsed_att_date()` 函数增加 `output_path` 参数
   - CLI 增加 `--output` / `-o` 参数指定保存路径

2. **`.agent/skills/teams-attendance/SKILL.md`**
   - 更新使用示例和参数说明

## 验证计划

### 手动验证
```bash
python .agent/skills/teams-attendance/scripts/fetch_attendance.py --month 2026-01 --output ./data/attendance_202601.csv
```
确认 CSV 文件生成且内容正确。
