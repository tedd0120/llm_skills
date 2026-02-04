---
description: 抓取国际黄金价格（COMEX期货/现货XAU）
---

# 伦敦金/国际金价数据抓取 Skill

使用 yfinance 库抓取 COMEX 黄金期货和现货黄金（XAU/USD）数据。

## 功能

1. **COMEX黄金期货** - GC=F 合约数据
2. **现货黄金** - XAU/USD 价格数据

## 使用方法

### 抓取 COMEX 黄金期货

```python
from scripts.fetch_london_gold import fetch_comex_gold_hist, save_to_csv

# 抓取 COMEX 黄金期货历史数据
df = fetch_comex_gold_hist(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
save_to_csv(df, "comex_gold.csv")
```

### 抓取现货黄金 (XAU/USD)

```python
from scripts.fetch_london_gold import fetch_xauusd_hist

df = fetch_xauusd_hist(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
print(df.head())
```

### 获取实时金价

```python
from scripts.fetch_london_gold import fetch_gold_realtime

price_info = fetch_gold_realtime()
print(f"当前金价: {price_info.get('regularMarketPrice')}")
```

## 品种说明

| 代码 | 说明 |
|-----|------|
| GC=F | COMEX 黄金期货（主力合约） |
| XAUUSD=X | 现货黄金 XAU/USD |
| GLD | SPDR 黄金 ETF |
