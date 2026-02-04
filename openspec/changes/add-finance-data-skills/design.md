# 设计文档：金融数据抓取 Skills 架构

## 上下文
需要创建一套可复用的金融数据抓取 skills，供 AI 编程助手调用。这些 skills 需要覆盖多个市场（A股、港股、美股）和资产类别（股票、基金、黄金）。

### 约束
- 必须使用 yfinance 和 akshare 两个库
- 数据需要持久化存储
- skills 需要遵循 `.agent/skills/` 的标准结构

## 目标 / 非目标

### 目标
- 建立统一的 skill 目录结构
- 每个 skill 独立可执行
- 提供清晰的使用说明（SKILL.md）
- 支持历史数据和实时数据抓取
- 数据持久化为 CSV/Parquet 格式

### 非目标
- 不实现实时推送/WebSocket
- 不构建完整的数据库系统
- 不实现复杂的数据清洗逻辑

## 决策

### 1. Skill 目录结构
```
.agent/skills/
├── finance-data-china-a-stock/
│   ├── SKILL.md              # 使用说明
│   └── scripts/
│       └── fetch_a_stock.py  # 抓取脚本
├── finance-data-fund/
│   ├── SKILL.md
│   └── scripts/
│       └── fetch_fund.py
├── finance-data-hk-stock/
│   ├── SKILL.md
│   └── scripts/
│       └── fetch_hk_stock.py
├── finance-data-us-stock/
│   ├── SKILL.md
│   └── scripts/
│       └── fetch_us_stock.py
├── finance-data-shanghai-gold/
│   ├── SKILL.md
│   └── scripts/
│       └── fetch_shanghai_gold.py
└── finance-data-london-gold/
    ├── SKILL.md
    └── scripts/
        └── fetch_london_gold.py
```

**理由**: 每个资产类别独立成一个 skill，便于维护和复用。

### 2. 数据存储策略
- 默认存储路径: `data/` 目录
- 文件格式: CSV (便于阅读) 和 Parquet (高效存储)
- 命名规则: `{asset_type}_{symbol}_{date_range}.csv`

**理由**: CSV 便于调试和人工检查，Parquet 适合大数据量场景。

### 3. API 选择策略
| 数据 | 库 | 函数 |
|------|-----|------|
| A股历史 | akshare | `stock_zh_a_hist(symbol, period, start_date, end_date)` |
| A股实时 | akshare | `stock_zh_a_spot_em()` |
| 基金净值 | akshare | `fund_open_fund_info_em(symbol, period)` |
| ETF历史 | akshare | `fund_etf_hist_em(symbol, period, start_date, end_date)` |
| 港股历史 | akshare | `stock_hk_hist(symbol, period, start_date, end_date)` |
| 美股历史 | yfinance | `yf.download(symbol, start, end)` |
| 沪金历史 | akshare | `spot_hist_sge(symbol)` |
| 伦敦金 | yfinance | `yf.download("GC=F", start, end)` |

## 风险 / 权衡

### 风险 1：API 限流或数据源不稳定
- **缓解**: 添加重试机制和请求间隔
- **缓解**: 提供错误处理和日志记录

### 风险 2：数据格式不一致
- **缓解**: 统一输出 DataFrame 格式
- **缓解**: 标准化列名（date, open, high, low, close, volume）

## 待决问题
- [ ] 是否需要支持增量数据更新？（建议后续迭代添加）
- [ ] 是否需要数据校验功能？（建议后续迭代添加）
