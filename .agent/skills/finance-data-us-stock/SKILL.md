---
description: 抓取美股历史行情和公司信息
---

# 美股数据抓取 Skill

使用 yfinance 库抓取美国股票市场数据。

## 功能

1. **历史行情数据** - 获取美股历史K线数据
2. **公司信息** - 获取公司基本信息、市值等

## 使用方法

### 抓取单只美股历史数据

```python
from scripts.fetch_us_stock import fetch_us_stock_hist, save_to_csv

# 抓取苹果公司历史数据
df = fetch_us_stock_hist(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
save_to_csv(df, "aapl_daily.csv")
```

### 批量抓取多只美股

```python
from scripts.fetch_us_stock import fetch_us_stocks_batch

# 批量抓取
symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
df = fetch_us_stocks_batch(symbols, "2024-01-01", "2024-03-31")
```

### 获取公司信息

```python
from scripts.fetch_us_stock import fetch_us_stock_info

info = fetch_us_stock_info("AAPL")
print(f"公司: {info.get('shortName')}")
print(f"市值: {info.get('marketCap')}")
```

## 参数说明

| 参数 | 类型 | 说明 |
|-----|------|-----|
| symbol | str | 股票代码，如 "AAPL", "GOOGL" |
| start_date | str | 开始日期 YYYY-MM-DD |
| end_date | str | 结束日期 YYYY-MM-DD |
