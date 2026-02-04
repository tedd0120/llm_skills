"""
港股数据抓取模块
使用 akshare（主）和 yfinance（备）获取香港股票市场数据
"""

import akshare as ak
import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime


def fetch_hk_stock_hist_akshare(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    adjust: str = "qfq"
) -> pd.DataFrame:
    """
    使用 akshare 获取港股历史行情数据
    
    Args:
        symbol: 港股代码，如 "00700"
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD
        adjust: 复权类型
    
    Returns:
        DataFrame 包含 OHLCV 数据
    """
    if start_date is None:
        start_date = "20200101"
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    try:
        df = ak.stock_hk_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        print(f"[akshare] 成功获取港股 {symbol} 的历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"[akshare] 获取港股数据失败: {e}")
        return pd.DataFrame()


def fetch_hk_stock_hist_yfinance(
    symbol: str,
    start_date: str = None,
    end_date: str = None
) -> pd.DataFrame:
    """
    使用 yfinance 获取港股历史行情数据（备选方案）
    
    Args:
        symbol: 港股代码，需要 .HK 后缀，如 "0700.HK"
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
    
    Returns:
        DataFrame 包含 OHLCV 数据
    """
    if start_date is None:
        start_date = "2020-01-01"
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if not df.empty:
            df = df.reset_index()
            print(f"[yfinance] 成功获取港股 {symbol} 的历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"[yfinance] 获取港股数据失败: {e}")
        return pd.DataFrame()


def fetch_hk_stock_realtime() -> pd.DataFrame:
    """
    获取港股实时行情
    
    Returns:
        DataFrame 包含港股实时行情
    """
    try:
        df = ak.stock_hk_spot_em()
        print(f"成功获取港股实时行情，共 {len(df)} 只股票")
        return df
    except Exception as e:
        print(f"获取港股实时行情失败: {e}")
        return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str, data_dir: str = "data") -> str:
    """将 DataFrame 保存为 CSV 文件"""
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    filepath = data_path / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"数据已保存到: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    # 测试：使用 akshare 抓取港股数据
    print("=" * 50)
    print("测试 港股历史数据抓取 (akshare)")
    print("=" * 50)
    
    df_ak = fetch_hk_stock_hist_akshare(
        symbol="00700",
        start_date="20240101",
        end_date="20240131"
    )
    if not df_ak.empty:
        print("\nakshare 数据预览:")
        print(df_ak.head())
        save_to_csv(df_ak, "hk_stock_00700_akshare.csv")
    
    print("\n" + "=" * 50)
    print("测试 港股历史数据抓取 (yfinance)")
    print("=" * 50)
    
    df_yf = fetch_hk_stock_hist_yfinance(
        symbol="0700.HK",
        start_date="2024-01-01",
        end_date="2024-01-31"
    )
    if not df_yf.empty:
        print("\nyfinance 数据预览:")
        print(df_yf.head())
        save_to_csv(df_yf, "hk_stock_0700_yfinance.csv")
    
    print("\n测试完成!")
