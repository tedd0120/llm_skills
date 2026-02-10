# 任务清单：增强 Alpha Vantage 新闻 Skill

## 1. 新增财报会议记录功能
- [x] 在 `fetch_news.py` 中实现 `fetch_earnings_call()` 函数
- [x] 解析 API 返回的 transcript 和 sentiment 字段
- [x] 更新 `SKILL.md` 添加使用说明
- **验证**: ✓ Python 语法检查通过

## 2. 新增涨跌幅排行功能
- [x] 在 `fetch_news.py` 中实现 `fetch_top_movers()` 函数
- [x] 返回包含 gainers/losers/most_traded 的字典
- [x] 更新 `SKILL.md` 添加使用说明
- **验证**: ✓ Python 语法检查通过

## 3. 新增内部人交易功能
- [x] 在 `fetch_news.py` 中实现 `fetch_insider_transactions()` 函数
- [x] 解析交易日期、人员、类型、金额等字段
- [x] 更新 `SKILL.md` 添加使用说明
- **验证**: ✓ Python 语法检查通过

## 4. 增强时间范围筛选
- [x] 在 `fetch_news()` 函数签名中添加 `time_from`、`time_to`、`sort` 参数
- [x] 更新文档说明时间格式 `YYYYMMDDTHHMM`
- **验证**: ✓ Python 语法检查通过

## 5. 代码质量
- [x] 添加 `_check_api_key()` 辅助函数
- [x] 确保所有新函数包含 docstring
- [x] SKILL.md 包含所有新功能的使用示例

## 完成状态
✓ 所有任务已完成 (2026-02-09)
