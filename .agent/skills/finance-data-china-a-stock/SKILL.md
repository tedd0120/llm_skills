---
description: 抓取中国A股历史行情和实时数据
---

# A股数据抓取 Skill

使用 akshare 库抓取中国A股市场数据。

## 功能

1. **历史行情数据** - 获取指定股票的日/周/月K线数据
2. **实时行情数据** - 获取全市场A股实时行情快照

## 使用方法

### 抓取单只股票历史数据

```python
from scripts.fetch_a_stock import fetch_a_stock_hist, save_to_csv

# 抓取平安银行(000001) 近一年日线数据
df = fetch_a_stock_hist(
    symbol="000001",
    period="daily",
    start_date="20240101",
    end_date="20241231"
)

# 保存到CSV
save_to_csv(df, "000001_daily.csv")
```

### 获取全市场实时行情

```python
from scripts.fetch_a_stock import fetch_a_stock_realtime

# 获取所有A股当前行情
df = fetch_a_stock_realtime()
print(df.head())
```

## 参数说明

| 参数 | 类型 | 说明 |
|-----|------|-----|
| symbol | str | 股票代码，如 "000001" |
| period | str | 周期: "daily", "weekly", "monthly" |
| start_date | str | 开始日期 YYYYMMDD |
| end_date | str | 结束日期 YYYYMMDD |

## 输出格式

DataFrame 包含以下列：
- `日期` - 交易日期
- `开盘` - 开盘价
- `最高` - 最高价
- `最低` - 最低价
- `收盘` - 收盘价
- `成交量` - 成交量
- `成交额` - 成交金额
