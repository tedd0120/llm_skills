# 功能：teams-attendance-csv-export

## 修改需求

### 需求：支持导出考勤明细到 CSV 文件

`parsed_att_date()` 函数**必须**支持可选的 `output_path` 参数，当提供该参数时**必须**将考勤明细 DataFrame 保存为 CSV 文件。

#### 场景：指定输出路径
- 调用 `parsed_att_date("2026-01", output_path="./data/att.csv")`
- **必须**在指定路径生成 CSV 文件
- **必须**返回与原有行为一致的 `[avg_hours, att_df]`

#### 场景：不指定输出路径
- 调用 `parsed_att_date("2026-01")`
- **禁止**生成任何文件
- **必须**保持原有行为不变

---

### 需求：CLI 支持输出路径参数

命令行接口**必须**支持 `--output` / `-o` 参数指定 CSV 保存路径。

#### 场景：命令行导出 CSV
- 运行 `python fetch_attendance.py --month 2026-01 --output ./att.csv`
- **必须**在指定路径生成 CSV 文件
