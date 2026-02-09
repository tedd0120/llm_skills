"""
时事热点新闻抓取模块
支持 akshare（国内）和 Alpha Vantage（国际）两个数据源
"""

try:
    import akshare as ak
except ImportError:
    ak = None

import pandas as pd
import requests
from typing import Optional, Literal
from datetime import datetime
import os
import json


# Alpha Vantage API 配置
ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY", "")
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# 支持的板块关键词映射
TOPIC_MAPPING = {
    "科技": "technology",
    "technology": "technology",
    "区块链": "blockchain",
    "blockchain": "blockchain",
    "财报": "earnings",
    "earnings": "earnings",
    "ipo": "ipo",
    "IPO": "ipo",
    "并购": "mergers_and_acquisitions",
    "mergers_and_acquisitions": "mergers_and_acquisitions",
    "金融市场": "financial_markets",
    "financial_markets": "financial_markets",
    "财政政策": "economy_fiscal",
    "economy_fiscal": "economy_fiscal",
    "货币政策": "economy_monetary",
    "economy_monetary": "economy_monetary",
    "宏观经济": "economy_macro",
    "economy_macro": "economy_macro",
    "能源交通": "energy_transportation",
    "energy_transportation": "energy_transportation",
    "生命科学": "life_sciences",
    "life_sciences": "life_sciences",
    "制造业": "manufacturing",
    "manufacturing": "manufacturing",
    "房地产": "real_estate",
    "real_estate": "real_estate",
    "零售批发": "retail_wholesale",
    "retail_wholesale": "retail_wholesale",
    "金融": "finance",
    "finance": "finance",
}


def is_a_stock_code(ticker: str) -> bool:
    """
    判断是否为 A股股票代码（6位纯数字）
    """
    return ticker.isdigit() and len(ticker) == 6


def _check_api_key() -> bool:
    """
    检查 Alpha Vantage API Key 是否已设置
    
    Returns:
        bool: API Key 是否有效
    """
    if not ALPHAVANTAGE_API_KEY:
        print("❌ 错误: 未设置 ALPHAVANTAGE_API_KEY 环境变量")
        print("   请设置环境变量后重试: export ALPHAVANTAGE_API_KEY=your_key")
        return False
    return True


def fetch_top_movers() -> dict:
    """
    获取美股涨跌幅和成交量排行
    
    Returns:
        dict with keys: 'gainers', 'losers', 'most_actively_traded'
        每个值为 DataFrame
    """
    if not _check_api_key():
        return {"gainers": pd.DataFrame(), "losers": pd.DataFrame(), "most_actively_traded": pd.DataFrame()}
    
    print(f"⚠️ Alpha Vantage API 调用提醒：每日免费额度仅 25 次")
    
    params = {
        "function": "TOP_GAINERS_LOSERS",
        "apikey": ALPHAVANTAGE_API_KEY
    }
    
    try:
        response = requests.get(ALPHAVANTAGE_BASE_URL, params=params)
        data = response.json()
        
        if "top_gainers" not in data:
            print(f"Alpha Vantage API 返回错误: {data.get('Note', data.get('Information', data))}")
            return {"gainers": pd.DataFrame(), "losers": pd.DataFrame(), "most_actively_traded": pd.DataFrame()}
        
        result = {
            "gainers": pd.DataFrame(data.get("top_gainers", [])),
            "losers": pd.DataFrame(data.get("top_losers", [])),
            "most_actively_traded": pd.DataFrame(data.get("most_actively_traded", []))
        }
        
        print(f"✓ 成功获取美股涨跌幅排行")
        return result
        
    except Exception as e:
        print(f"Alpha Vantage API 调用失败: {e}")
        return {"gainers": pd.DataFrame(), "losers": pd.DataFrame(), "most_actively_traded": pd.DataFrame()}


def fetch_insider_transactions(symbol: str) -> pd.DataFrame:
    """
    获取公司内部人士交易记录
    
    Args:
        symbol: 股票代码，如 "IBM"
    
    Returns:
        DataFrame 包含内部人交易详情
    """
    if not _check_api_key():
        return pd.DataFrame()
    
    print(f"⚠️ Alpha Vantage API 调用提醒：每日免费额度仅 25 次")
    
    params = {
        "function": "INSIDER_TRANSACTIONS",
        "symbol": symbol,
        "apikey": ALPHAVANTAGE_API_KEY
    }
    
    try:
        response = requests.get(ALPHAVANTAGE_BASE_URL, params=params)
        data = response.json()
        
        if "data" not in data:
            print(f"Alpha Vantage API 返回错误: {data.get('Note', data.get('Information', data))}")
            return pd.DataFrame()
        
        transactions = data.get("data", [])
        
        # 解析交易记录
        records = []
        for tx in transactions:
            records.append({
                "transaction_date": tx.get("transaction_date", ""),
                "insider_name": tx.get("executive", ""),
                "insider_title": tx.get("executive_title", ""),
                "transaction_type": tx.get("acquisition_or_disposal", ""),
                "shares": tx.get("shares", 0),
                "value": tx.get("share_price", 0)
            })
        
        df = pd.DataFrame(records)
        print(f"✓ 成功获取 {symbol} 内部人交易记录，共 {len(df)} 条")
        return df
        
    except Exception as e:
        print(f"Alpha Vantage API 调用失败: {e}")
        return pd.DataFrame()


def fetch_stock_news_akshare(ticker: str) -> pd.DataFrame:
    """
    使用 akshare 抓取 A股个股新闻
    
    Args:
        ticker: 股票代码，如 "000001"
    
    Returns:
        DataFrame 包含新闻标题、内容、发布时间、链接
    """
    if ak is None:
        print("❌ 错误: 未安装 akshare 库，无法抓取 A股新闻")
        print("   请运行: pip install akshare")
        return pd.DataFrame()
        
    try:
        df = ak.stock_news_em(symbol=ticker)
        # 统一列名
        df = df.rename(columns={
            "新闻标题": "title",
            "新闻内容": "summary", 
            "发布时间": "published_time",
            "新闻链接": "url",
            "文章来源": "source"
        })
        # 添加缺失列
        df["sentiment_score"] = None
        df["tickers"] = ticker
        print(f"成功获取 {ticker} 的新闻，共 {len(df)} 条")
        return df
    except Exception as e:
        print(f"akshare 抓取新闻失败: {e}")
        return pd.DataFrame()


def fetch_news_alphavantage(
    tickers: Optional[str] = None,
    topics: Optional[str] = None,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    sort: str = "LATEST",
    limit: int = 50,
    target_ticker: Optional[str] = None
) -> pd.DataFrame:
    """
    使用 Alpha Vantage API 抓取新闻
    
    Args:
        tickers: 股票代码，如 "AAPL" 或 "AAPL,GOOGL"
        topics: 主题关键词，如 "technology" 或 "technology,ipo"
        time_from: 开始时间 YYYYMMDDTHHMM
        time_to: 结束时间 YYYYMMDDTHHMM
        sort: 排序方式 LATEST/EARLIEST/RELEVANCE
        limit: 返回条数，默认50，最大1000
        target_ticker: 目标股票代码，用于提取该股票的专属情绪
    
    Returns:
        DataFrame 包含新闻和情绪分析数据
    """
    print(f"⚠️ Alpha Vantage API 调用提醒：每日免费额度仅 25 次")
    
    params = {
        "function": "NEWS_SENTIMENT",
        "apikey": ALPHAVANTAGE_API_KEY,
        "sort": sort,
        "limit": limit
    }
    
    if tickers:
        params["tickers"] = tickers
    if topics:
        params["topics"] = topics
    if time_from:
        params["time_from"] = time_from
    if time_to:
        params["time_to"] = time_to
    
    try:
        response = requests.get(ALPHAVANTAGE_BASE_URL, params=params)
        data = response.json()
        
        if "feed" not in data:
            print(f"Alpha Vantage API 返回错误: {data.get('Note', data.get('Information', data))}")
            return pd.DataFrame()
        
        articles = data["feed"]
        
        # 解析新闻数据
        news_list = []
        for article in articles:
            # 解析 ticker_sentiment
            ticker_sentiments = article.get("ticker_sentiment", [])
            
            # 提取目标股票的专属情绪
            target_sentiment = None
            target_label = None
            if target_ticker:
                for ts in ticker_sentiments:
                    if ts.get("ticker") == target_ticker:
                        target_sentiment = float(ts.get("ticker_sentiment_score", 0))
                        target_label = ts.get("ticker_sentiment_label", "")
                        break
            
            # 解析 topics
            article_topics = article.get("topics", [])
            topics_str = ",".join([f"{t['topic']}:{t['relevance_score']}" for t in article_topics])
            
            news_item = {
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "published_time": article.get("time_published", ""),
                "sentiment_score": article.get("overall_sentiment_score", None),
                "sentiment_label": article.get("overall_sentiment_label", ""),
                "tickers": ",".join([t["ticker"] for t in ticker_sentiments]),
                "ticker_sentiments": json.dumps(ticker_sentiments),
                "topics": topics_str,
                "target_ticker_sentiment": target_sentiment,
                "target_ticker_label": target_label
            }
            news_list.append(news_item)
        
        df = pd.DataFrame(news_list)
        print(f"成功获取新闻，共 {len(df)} 条")
        return df
        
    except Exception as e:
        print(f"Alpha Vantage API 调用失败: {e}")
        return pd.DataFrame()


def fetch_news(
    query_type: Literal["global", "sector", "ticker"] = "global",
    keyword: Optional[str] = None,
    ticker: Optional[str] = None,
    source: Literal["auto", "akshare", "alphavantage"] = "auto",
    limit: int = 50,
    time_from: Optional[str] = None,
    time_to: Optional[str] = None,
    sort: Literal["LATEST", "EARLIEST", "RELEVANCE"] = "LATEST"
) -> pd.DataFrame:
    """
    统一新闻抓取接口
    
    Args:
        query_type: 查询类型
            - "global": 全球宏观新闻
            - "sector": 板块关键词新闻
            - "ticker": 个股新闻
        keyword: 板块关键词（query_type="sector" 时使用）
        ticker: 股票代码（query_type="ticker" 时使用）
        source: 数据源选择
            - "auto": 自动选择（A股用akshare，其他用alphavantage）
            - "akshare": 强制使用akshare
            - "alphavantage": 强制使用Alpha Vantage
        limit: 返回条数限制
        time_from: 开始时间，格式 YYYYMMDDTHHMM（仅 Alpha Vantage）
        time_to: 结束时间，格式 YYYYMMDDTHHMM（仅 Alpha Vantage）
        sort: 排序方式 LATEST/EARLIEST/RELEVANCE（仅 Alpha Vantage）
    
    Returns:
        DataFrame 包含统一格式的新闻数据
    """
    
    # 全球宏观新闻
    if query_type == "global":
        return fetch_news_alphavantage(
            topics="economy_macro,financial_markets",
            limit=limit,
            time_from=time_from,
            time_to=time_to,
            sort=sort
        )
    
    # 板块关键词新闻
    if query_type == "sector":
        if not keyword:
            print("错误: 板块查询需要指定 keyword 参数")
            return pd.DataFrame()
        
        # 转换中文关键词
        topic = TOPIC_MAPPING.get(keyword, keyword)
        return fetch_news_alphavantage(
            topics=topic,
            limit=limit,
            time_from=time_from,
            time_to=time_to,
            sort=sort
        )
    
    # 个股新闻
    if query_type == "ticker":
        if not ticker:
            print("错误: 个股查询需要指定 ticker 参数")
            return pd.DataFrame()
        
        # 自动选择数据源
        if source == "auto":
            if is_a_stock_code(ticker):
                source = "akshare"
            else:
                source = "alphavantage"
        
        if source == "akshare":
            if time_from or time_to:
                print("⚠️ 警告: akshare 数据源不支持时间范围筛选，参数将被忽略")
            return fetch_stock_news_akshare(ticker)
        else:
            return fetch_news_alphavantage(
                tickers=ticker,
                limit=limit,
                time_from=time_from,
                time_to=time_to,
                sort=sort,
                target_ticker=ticker
            )
    
    print(f"错误: 不支持的查询类型 {query_type}")
    return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str, data_dir: str = "data") -> str:
    """
    将 DataFrame 保存为 CSV 文件
    """
    from pathlib import Path
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    filepath = data_path / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"数据已保存到: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    print("=" * 60)
    print("测试 1: A股个股新闻抓取 (akshare)")
    print("=" * 60)
    
    df_a_stock = fetch_news(query_type="ticker", ticker="000001")
    if not df_a_stock.empty:
        print("\n新闻预览 (前3条):")
        print(df_a_stock[["title", "published_time"]].head(3))
        save_to_csv(df_a_stock, "news_000001_sample.csv")
    
    print("\n" + "=" * 60)
    print("测试 2: 全球宏观新闻 (Alpha Vantage)")
    print("⚠️ 注意: 此调用会消耗 API 额度，仅运行一次")
    print("=" * 60)
    
    df_global = fetch_news(query_type="global", limit=10)
    if not df_global.empty:
        print("\n新闻预览 (前3条):")
        print(df_global[["title", "sentiment_score"]].head(3))
        save_to_csv(df_global, "news_global_sample.csv")
    
    print("\n测试完成!")
