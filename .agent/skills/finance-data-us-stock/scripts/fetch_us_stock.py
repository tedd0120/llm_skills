"""
美股数据抓取模块
使用 yfinance 库获取美国股票市场数据
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def fetch_us_stock_hist(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    获取美股历史行情数据
    
    Args:
        symbol: 股票代码，如 "AAPL"
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        interval: 数据间隔，如 "1d", "1wk", "1mo"
    
    Returns:
        DataFrame 包含 OHLCV 数据
    """
    if start_date is None:
        start_date = "2020-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        df = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False)
        if not df.empty:
            df = df.reset_index()
            print(f"成功获取 {symbol} 的历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取美股数据失败: {e}")
        return pd.DataFrame()


def fetch_us_stocks_batch(
    symbols: List[str],
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    批量获取多只美股历史数据
    
    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        DataFrame 包含所有股票数据（多层索引）
    """
    if start_date is None:
        start_date = "2020-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        df = yf.download(symbols, start=start_date, end=end_date, progress=False)
        print(f"成功批量获取 {len(symbols)} 只股票的历史数据")
        return df
    except Exception as e:
        print(f"批量获取美股数据失败: {e}")
        return pd.DataFrame()


def fetch_us_stock_info(symbol: str) -> Dict[str, Any]:
    """
    获取美股公司基本信息
    
    Args:
        symbol: 股票代码
    
    Returns:
        包含公司信息的字典
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"成功获取 {symbol} 的公司信息")
        return info
    except Exception as e:
        print(f"获取公司信息失败: {e}")
        return {}


def save_to_csv(df: pd.DataFrame, filename: str, data_dir: str = "data") -> str:
    """将 DataFrame 保存为 CSV 文件"""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    filepath = data_path / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"数据已保存到: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    # 测试：抓取苹果公司历史数据
    print("=" * 50)
    print("测试 美股历史数据抓取")
    print("=" * 50)
    
    df_hist = fetch_us_stock_hist(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    if not df_hist.empty:
        print("\n历史数据预览:")
        print(df_hist.head())
        save_to_csv(df_hist, "us_stock_aapl_sample.csv")
    
    print("\n" + "=" * 50)
    print("测试 美股公司信息获取")
    print("=" * 50)
    
    info = fetch_us_stock_info("AAPL")
    if info:
        print(f"\n公司名称: {info.get('shortName', 'N/A')}")
        print(f"行业: {info.get('industry', 'N/A')}")
        print(f"市值: {info.get('marketCap', 'N/A')}")
    
    print("\n测试完成!")
