# LLM Skills

给 LLM 写的技能插件。

## 功能

插件化获取金融数据。架构通用，可扩展。

## Skills

| Skill | 功能 | 数据源 |
|-------|------|--------|
| `finance-data-china-a-stock` | A股K线 + 实时快照 | akshare |
| `finance-data-hk-stock` | 港股数据 | akshare / yfinance |
| `finance-data-us-stock` | 美股行情 + 基本面 | yfinance |
| `finance-data-fund` | 基金净值 + ETF | akshare |
| `finance-data-shanghai-gold` | 沪金现货 | akshare |
| `finance-data-london-gold` | COMEX + XAU/USD | yfinance |
| `finance-data-news` | 财经新闻 + 情绪 | akshare / Alpha Vantage |

## 使用

每个 skill 在 `.agent/skills/` 下都有 `SKILL.md`。

```
.agent/skills/
├── finance-data-china-a-stock/
├── finance-data-fund/
├── finance-data-hk-stock/
├── finance-data-london-gold/
├── finance-data-news/
├── finance-data-shanghai-gold/
└── finance-data-us-stock/
```

## 依赖

```bash
pip install akshare yfinance python-dotenv requests
```

## 注意

- Alpha Vantage 免费版限 25 次/天
- API Key 放 `.env`
