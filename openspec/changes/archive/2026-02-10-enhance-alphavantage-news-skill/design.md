# 设计文档：增强 Alpha Vantage 新闻 Skill

## 上下文

现有 `finance-data-news` skill 提供了基础的新闻抓取能力，但 Alpha Vantage 的 Alpha Intelligence™ 套件还包含多个高价值 API：
- **EARNINGS_CALL_TRANSCRIPT** - 财报电话会议记录（覆盖2010年至今）
- **TOP_GAINERS_LOSERS** - 美股涨跌幅Top 20
- **INSIDER_TRANSACTIONS** - 内部人士交易记录

这些数据对于投资研究和市场分析具有重要参考价值。

## 目标 / 非目标

### 目标
- 新增财报会议记录查询函数 `fetch_earnings_call()`
- 新增涨跌幅排行查询函数 `fetch_top_movers()`
- 新增内部人交易查询函数 `fetch_insider_transactions()`
- 增强现有新闻查询的时间范围筛选能力
- 保持与现有接口风格一致

### 非目标
- 不实现 Advanced Analytics API（需要 Premium 套餐的完整功能）
- 不实现数据缓存机制
- 不改变现有 `fetch_news()` 函数的参数签名

## 决策

### 1. API 函数设计

#### 1.1 财报会议记录

```python
def fetch_earnings_call(
    symbol: str,
    quarter: str  # 格式: "2024Q1"
) -> pd.DataFrame:
    """
    获取公司财报电话会议记录
    
    Returns:
        DataFrame with columns: transcript, sentiment, quarter, symbol
    """
```

**API 端点**: `function=EARNINGS_CALL_TRANSCRIPT&symbol=IBM&quarter=2024Q1`

**返回字段**:
- `transcript` - 完整记录文本
- `sentiment` - LLM 情绪分析
- `quarter` - 财报季度
- `symbol` - 股票代码

#### 1.2 涨跌幅排行榜

```python
def fetch_top_movers() -> dict[str, pd.DataFrame]:
    """
    获取美股涨跌幅和成交量排行
    
    Returns:
        dict with keys: 'gainers', 'losers', 'most_actively_traded'
    """
```

**API 端点**: `function=TOP_GAINERS_LOSERS`

**返回结构**:
```python
{
    "gainers": DataFrame,       # 涨幅 Top 20
    "losers": DataFrame,        # 跌幅 Top 20
    "most_actively_traded": DataFrame  # 成交量 Top 20
}
```

#### 1.3 内部人交易记录

```python
def fetch_insider_transactions(symbol: str) -> pd.DataFrame:
    """
    获取公司内部人士交易记录
    
    Returns:
        DataFrame with insider transaction details
    """
```

**API 端点**: `function=INSIDER_TRANSACTIONS&symbol=IBM`

**返回字段**:
- `transaction_date` - 交易日期
- `insider_name` - 内部人姓名
- `insider_title` - 职位
- `transaction_type` - 买入/卖出
- `shares` - 股数
- `value` - 交易金额

### 2. 时间范围筛选增强

在现有 `fetch_news()` 函数中增加可选参数：

```python
def fetch_news(
    query_type: Literal["global", "sector", "ticker"] = "global",
    keyword: Optional[str] = None,
    ticker: Optional[str] = None,
    source: Literal["auto", "akshare", "alphavantage"] = "auto",
    limit: int = 50,
    # 新增参数
    time_from: Optional[str] = None,  # YYYYMMDDTHHMM
    time_to: Optional[str] = None,    # YYYYMMDDTHHMM
    sort: Literal["LATEST", "EARLIEST", "RELEVANCE"] = "LATEST"
) -> pd.DataFrame:
```

### 3. 错误处理

所有新函数遵循现有模式：
- API 调用失败返回空 DataFrame
- 打印友好的错误提示
- 不抛出异常中断执行

### 4. API Key 检查

在调用前统一检查 API Key：

```python
def _check_api_key() -> bool:
    if not ALPHAVANTAGE_API_KEY:
        print("错误: 未设置 ALPHAVANTAGE_API_KEY 环境变量")
        return False
    return True
```

## 风险 / 权衡

### 风险 1：API 额度消耗增加
- **问题**: 新增3个功能，可能加速消耗每日25次额度
- **缓解**: 
  - 文档中强调合理使用
  - 每次调用打印额度提醒
  - 财报会议记录建议按需查询特定季度

### 风险 2：财报会议记录数据量大
- **问题**: 单次返回的 transcript 文本可能很长
- **缓解**: 返回结构中保持原始格式，由调用方决定如何处理

### 风险 3：涨跌幅数据时效性
- **问题**: 免费用户获取的数据是收盘后数据，非实时
- **缓解**: 文档中说明数据更新时机

## 待决问题
- [ ] 是否需要将涨跌幅数据缓存到本地？→ 暂不实现
- [ ] 是否需要支持批量查询多个股票的内部人交易？→ 当前 API 不支持
