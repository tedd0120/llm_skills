---
description: 抓取基金净值和ETF历史数据
---

# 基金数据抓取 Skill

使用 akshare 库抓取公募基金和ETF数据。

## 功能

1. **开放式基金净值** - 获取基金历史净值数据
2. **ETF历史行情** - 获取ETF的K线数据

## 使用方法

### 抓取开放式基金净值

```python
from scripts.fetch_fund import fetch_fund_nav

# 抓取易方达蓝筹精选基金净值
df = fetch_fund_nav(fund_code="005827")
print(df.head())
```

### 抓取ETF历史数据

```python
from scripts.fetch_fund import fetch_etf_hist, save_to_csv

# 抓取沪深300ETF历史数据
df = fetch_etf_hist(
    symbol="510300",
    start_date="20240101",
    end_date="20241231"
)
save_to_csv(df, "etf_510300.csv")
```

## 参数说明

| 参数 | 类型 | 说明 |
|-----|------|-----|
| fund_code | str | 基金代码，如 "005827" |
| symbol | str | ETF代码，如 "510300" |
| start_date | str | 开始日期 YYYYMMDD |
| end_date | str | 结束日期 YYYYMMDD |

## 输出格式

### 基金净值
- `净值日期` - 日期
- `单位净值` - 每份净值
- `累计净值` - 累计净值
- `日增长率` - 日涨跌幅

### ETF行情
- OHLCV 格式（日期、开盘、最高、最低、收盘、成交量）
