# 任务清单：增强新闻情绪解析

## 1. 个股专属情绪解析
- [x] 修改 `fetch_news_alphavantage()` 解析 `ticker_sentiment` 字段
- [x] 新增 `ticker_sentiments` 列（JSON 格式）
- [x] 新增 `target_ticker` 参数
- [x] 新增 `target_ticker_sentiment` 和 `target_ticker_label` 列
- **验证**: ✓ Python 语法检查通过

## 2. 话题标签解析
- [x] 解析 API 返回的 `topics` 字段
- [x] 新增 `topics` 列，格式 "topic:score,topic:score"
- **验证**: ✓ Python 语法检查通过

## 3. 传递 target_ticker
- [x] 修改 `fetch_news()` 在 ticker 查询时传递 `target_ticker`
- **验证**: ✓ Python 语法检查通过

## 4. 文档更新
- [x] 更新 SKILL.md 说明新增列
- [x] 添加使用示例

## 完成状态
✓ 所有任务已完成 (2026-02-09)
