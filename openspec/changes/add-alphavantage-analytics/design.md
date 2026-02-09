# 设计文档

## 架构变更
在 `finance-data-news` Skill 中增加新的脚本文件。虽然 Skill 名称包含 `news`，但为了避免创建过多的微型 Skill 或大规模重构重命名（这可能会破坏现有引用），建议将这些新的 AlphaVantage 功能整合到现有的 `finance-data-news` 目录下，该目录实际上已经充当了 "AlphaVantage Integration" 的角色（包含 Top Movers, Insider 等非新闻功能）。

未来如果功能过于庞大，可以考虑将 `finance-data-news` 重命名为 `finance-data-alphavantage` 或拆分，但在本提案阶段保持目录结构稳定。

## 新增脚本
在 `finance-data-news/scripts/` 下增加以下模块：

1.  **`fetch_fundamentals.py`**
    *   封装 Alpha Vantage Fundamental Data API。
    *   主要函数：`fetch_company_overview`, `fetch_financials` (统一入口或分拆为 `fetch_income_statement` 等)。

2.  **`fetch_economics.py`**
    *   封装 Alpha Vantage Economic Indicators API。
    *   主要函数：`fetch_economic_indicator(indicator_name, **kwargs)` 通用函数，或具体函数如 `fetch_real_gdp`。建议采用通用函数 `fetch_economic_indicator` 并提供常量/枚举支持。

3.  **`fetch_technicals.py`**
    *   封装 Alpha Vantage Technical Indicators API。
    *   主要函数：`fetch_technical_indicator(function, symbol, interval, time_period, series_type, **kwargs)` 通用入口。

4.  **`fetch_commodities.py`**
    *   封装 Alpha Vantage Commodities API。
    *   主要函数：`fetch_commodity(commodity_type, interval, **kwargs)`。

## 接口设计
函数应保持与 `fetch_news` 类似的风格：
*   **输入**: 必须参数（名）+ 可选参数（`**kwargs` 或 明确列出）。
*   **输出**: 统一返回 `pandas.DataFrame` 以便于后续数据分析和绘图。对于单一数值的时间序列，DataFrame 为 `date` + `value` 列；对于多维数据（如 MACD），为 `date` + `MACD_Signal`, `MACD_Hist`, `MACD` 等列。
*   **错误处理**: 捕获 API 限制或网络错误，并友好返回或抛出。
*   **API Key**: 自动均从环境变量 `ALPHAVANTAGE_API_KEY` 读取。
