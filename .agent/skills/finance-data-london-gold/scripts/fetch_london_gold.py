"""
伦敦金/国际金价数据抓取模块
使用 yfinance 库获取 COMEX 黄金期货和现货黄金数据
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def fetch_comex_gold_hist(
    start_date: str = None,
    end_date: str = None,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    获取 COMEX 黄金期货历史数据
    
    Args:
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        interval: 数据间隔
    
    Returns:
        DataFrame 包含 OHLCV 数据
    """
    if start_date is None:
        start_date = "2020-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        df = yf.download("GC=F", start=start_date, end=end_date, interval=interval, progress=False)
        if not df.empty:
            df = df.reset_index()
            print(f"成功获取 COMEX 黄金期货历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取 COMEX 金价失败: {e}")
        return pd.DataFrame()


def fetch_xauusd_hist(
    start_date: str = None,
    end_date: str = None,
    interval: str = "1d"
) -> pd.DataFrame:
    """
    获取现货黄金 XAU/USD 历史数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        interval: 数据间隔
    
    Returns:
        DataFrame 包含 OHLCV 数据
    """
    if start_date is None:
        start_date = "2020-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        df = yf.download("XAUUSD=X", start=start_date, end=end_date, interval=interval, progress=False)
        if not df.empty:
            df = df.reset_index()
            print(f"成功获取现货黄金 XAU/USD 历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取现货金价失败: {e}")
        return pd.DataFrame()


def fetch_gold_realtime(symbol: str = "GC=F") -> Dict[str, Any]:
    """
    获取黄金实时价格
    
    Args:
        symbol: 品种代码，默认 "GC=F" (COMEX期货)
    
    Returns:
        包含实时价格信息的字典
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        print(f"成功获取 {symbol} 实时价格")
        return info
    except Exception as e:
        print(f"获取实时金价失败: {e}")
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
    # 测试：抓取 COMEX 黄金期货
    print("=" * 50)
    print("测试 COMEX 黄金期货历史数据抓取")
    print("=" * 50)
    
    df_comex = fetch_comex_gold_hist(
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    if not df_comex.empty:
        print("\nCOMEX 黄金期货数据预览:")
        print(df_comex.head())
        save_to_csv(df_comex, "comex_gold_sample.csv")
    
    print("\n" + "=" * 50)
    print("测试 现货黄金 XAU/USD 历史数据抓取")
    print("=" * 50)
    
    df_xau = fetch_xauusd_hist(
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    if not df_xau.empty:
        print("\n现货黄金数据预览:")
        print(df_xau.head())
        save_to_csv(df_xau, "xauusd_sample.csv")
    
    print("\n" + "=" * 50)
    print("测试 黄金实时价格获取")
    print("=" * 50)
    
    info = fetch_gold_realtime("GC=F")
    if info:
        print(f"\n当前价格: {info.get('regularMarketPrice', 'N/A')}")
        print(f"货币: {info.get('currency', 'N/A')}")
    
    print("\n测试完成!")
