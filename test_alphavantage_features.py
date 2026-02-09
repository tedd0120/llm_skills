import os
import pandas as pd
from dotenv import load_dotenv
import sys

# 设置路径以便导入 scripts
sys.path.append(os.path.join(os.getcwd(), ".agent", "skills", "finance-data-news"))

# 加载环境变量
load_dotenv()

from scripts.fetch_news import (
    fetch_news, 
    fetch_top_movers, 
    fetch_earnings_call, 
    fetch_insider_transactions
)

def run_tests():
    print("🚀 开始 Alpha Vantage 增强功能验证测试...\n")
    
    # 1. 验证个股情绪和话题解析 (Targeted Ticker)
    print("--- 测试 1: 个股专属情绪与话题解析 (AAPL) ---")
    df_aapl = fetch_news(query_type="ticker", ticker="AAPL", limit=3)
    if not df_aapl.empty:
        print(f"成功获取 {len(df_aapl)} 条新闻")
        cols = ["title", "target_ticker_sentiment", "target_ticker_label", "topics"]
        print(df_aapl[cols].head())
    print("\n")

    # 2. 验证涨跌幅排行
    print("--- 测试 2: 涨跌幅排行榜 ---")
    movers = fetch_top_movers()
    print(f"成功获取涨幅榜: {len(movers.get('gainers', []))} 条")
    print(movers.get('gainers', pd.DataFrame())[['ticker', 'price', 'change_percentage']].head())
    print("\n")

    # 3. 验证内部人交易
    print("--- 测试 3: 内部人交易 (IBM) ---")
    insiders = fetch_insider_transactions("IBM")
    if not insiders.empty:
        print(f"成功获取 {len(insiders)} 条交易记录")
        print(insiders[['transaction_date', 'insider_name', 'transaction_type', 'shares']].head())
    print("\n")

    # 4. 验证财报会议记录 (可选，消耗次数较多)
    print("--- 测试 4: 财报会议记录 (IBM 2024Q1) ---")
    transcript = fetch_earnings_call("IBM", "2024Q1")
    if not transcript.empty:
        print("成功获取财报会议摘要:")
        print(f"Symbol: {transcript.iloc[0]['symbol']}, Quarter: {transcript.iloc[0]['quarter']}")
        print(f"Transcript (前100字): {transcript.iloc[0]['transcript'][:100]}...")
    print("\n")

if __name__ == "__main__":
    run_tests()
