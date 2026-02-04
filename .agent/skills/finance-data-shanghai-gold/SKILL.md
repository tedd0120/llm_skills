---
description: 抓取上海黄金交易所黄金现货数据
---

# 沪金数据抓取 Skill

使用 akshare 库抓取上海黄金交易所（SGE）黄金现货历史数据。

## 功能

1. **历史行情数据** - 获取沪金 Au9999 等品种历史数据

## 使用方法

### 抓取沪金历史数据

```python
from scripts.fetch_shanghai_gold import fetch_sge_gold_hist, save_to_csv

# 抓取 Au9999 历史数据
df = fetch_sge_gold_hist(symbol="Au9999")
print(df.head())
save_to_csv(df, "sge_au9999.csv")
```

### 查询可用品种

```python
from scripts.fetch_shanghai_gold import get_sge_symbols

symbols = get_sge_symbols()
print(symbols)  # ['Au9999', 'Au9995', 'Au100g', 'mAu', ...]
```

## 支持的品种

| 品种代码 | 说明 |
|---------|------|
| Au9999 | 黄金9999 |
| Au9995 | 黄金9995 |
| Au100g | 100克黄金 |
| mAu | 迷你黄金 |
| Au(T+D) | 黄金T+D |
| Ag(T+D) | 白银T+D |

## 输出格式

DataFrame 包含以下列：
- 日期、开盘价、最高价、最低价、收盘价、成交量
