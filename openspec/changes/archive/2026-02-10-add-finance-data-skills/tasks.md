# 任务清单：添加金融数据抓取 Skills

## 1. 环境准备
- [ ] 1.1 验证 Python 环境已安装
- [ ] 1.2 安装依赖: `pip install yfinance akshare pandas`
- [ ] 1.3 创建 `.agent/skills/` 目录结构

## 2. 实现 A股数据抓取 Skill
- [ ] 2.1 创建 `finance-data-china-a-stock/SKILL.md`
- [ ] 2.2 创建 `scripts/fetch_a_stock.py`
- [ ] 2.3 测试抓取示例股票（如 000001.SZ）

## 3. 实现基金数据抓取 Skill
- [ ] 3.1 创建 `finance-data-fund/SKILL.md`
- [ ] 3.2 创建 `scripts/fetch_fund.py`（支持 ETF 和开放式基金）
- [ ] 3.3 测试抓取示例基金

## 4. 实现港股数据抓取 Skill
- [ ] 4.1 创建 `finance-data-hk-stock/SKILL.md`
- [ ] 4.2 创建 `scripts/fetch_hk_stock.py`
- [ ] 4.3 测试抓取示例港股（如 00700.HK）

## 5. 实现美股数据抓取 Skill
- [ ] 5.1 创建 `finance-data-us-stock/SKILL.md`
- [ ] 5.2 创建 `scripts/fetch_us_stock.py`
- [ ] 5.3 测试抓取示例美股（如 AAPL）

## 6. 实现沪金数据抓取 Skill
- [ ] 6.1 创建 `finance-data-shanghai-gold/SKILL.md`
- [ ] 6.2 创建 `scripts/fetch_shanghai_gold.py`
- [ ] 6.3 测试抓取上海黄金交易所数据

## 7. 实现伦敦金数据抓取 Skill
- [ ] 7.1 创建 `finance-data-london-gold/SKILL.md`
- [ ] 7.2 创建 `scripts/fetch_london_gold.py`
- [ ] 7.3 测试抓取 COMEX 黄金期货数据

## 8. 验证和文档
- [ ] 8.1 验证所有 skill 可正常执行
- [ ] 8.2 创建 walkthrough 文档展示结果
