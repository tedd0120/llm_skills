---
description: 抓取港股历史行情和实时数据
---

# 港股数据抓取 Skill

使用 akshare（主）和 yfinance（备）抓取香港股票市场数据。

## 功能

1. **历史行情数据** - 获取港股历史K线数据
2. **实时行情** - 获取港股实时行情快照

## 使用方法

### 使用 akshare 抓取港股数据

```python
from scripts.fetch_hk_stock import fetch_hk_stock_hist_akshare

# 抓取腾讯(00700)历史数据
df = fetch_hk_stock_hist_akshare(
    symbol="00700",
    start_date="20240101",
    end_date="20241231"
)
print(df.head())
```

### 使用 yfinance 抓取港股数据（备选）

```python
from scripts.fetch_hk_stock import fetch_hk_stock_hist_yfinance

# 使用 yfinance 抓取
df = fetch_hk_stock_hist_yfinance(
    symbol="0700.HK",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

## 参数说明

| 参数 | 类型 | 说明 |
|-----|------|-----|
| symbol | str | 港股代码，akshare用 "00700"，yfinance用 "0700.HK" |
| start_date | str | 开始日期 |
| end_date | str | 结束日期 |

## 注意事项

- akshare 使用 5 位港股代码（如 00700）
- yfinance 使用 `.HK` 后缀（如 0700.HK）
