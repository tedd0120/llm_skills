# 任务清单：新增时事热点新闻抓取 Skill

## 1. 环境准备
- [x] 1.1 验证 akshare 已安装
- [x] 1.2 安装 requests 库用于 Alpha Vantage API 调用
- [x] 1.3 创建 `.agent/skills/finance-data-news/` 目录结构

## 2. 实现 akshare 新闻抓取
- [x] 2.1 实现 `fetch_stock_news_akshare()` 函数 - 抓取个股新闻
- [x] 2.2 支持 A股股票代码解析
- [x] 2.3 测试抓取示例（如 000001 平安银行）✅ 成功获取10条新闻

## 3. 实现 Alpha Vantage 新闻抓取
- [x] 3.1 实现 `fetch_news_alphavantage()` 函数 - 调用 NEWS_SENTIMENT API
- [x] 3.2 支持 ticker 查询（个股代码）
- [x] 3.3 支持 topics 查询（板块关键词）
- [x] 3.4 支持 global macro 查询（全球宏观）
- [x] 3.5 测试抓取示例 ✅ 成功获取50条全球新闻

## 4. 统一接口封装
- [x] 4.1 实现 `fetch_news()` 统一入口函数
- [x] 4.2 自动路由到对应数据源
- [x] 4.3 统一输出 DataFrame 格式

## 5. 文档和验证
- [x] 5.1 创建 `SKILL.md` 使用说明
- [x] 5.2 验证脚本可独立执行
- [x] 5.3 输出示例数据到 CSV
