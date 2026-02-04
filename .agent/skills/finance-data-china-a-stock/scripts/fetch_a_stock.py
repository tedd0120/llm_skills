"""
A股数据抓取模块
使用 akshare 库获取中国A股市场数据
"""

import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime


def fetch_a_stock_hist(
    symbol: str,
    period: str = "daily",
    start_date: str = None,
    end_date: str = None,
    adjust: str = "qfq"
) -> pd.DataFrame:
    """
    获取A股历史行情数据
    
    Args:
        symbol: 股票代码，如 "000001"
        period: 周期，可选 "daily", "weekly", "monthly"
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD
        adjust: 复权类型，"qfq"前复权, "hfq"后复权, ""不复权
    
    Returns:
        DataFrame 包含 OHLCV 数据
    """
    if start_date is None:
        start_date = "20200101"
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        print(f"成功获取 {symbol} 的历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取数据失败: {e}")
        return pd.DataFrame()


def fetch_a_stock_realtime() -> pd.DataFrame:
    """
    获取A股全市场实时行情
    
    Returns:
        DataFrame 包含所有A股当前行情
    """
    try:
        df = ak.stock_zh_a_spot_em()
        print(f"成功获取A股实时行情，共 {len(df)} 只股票")
        return df
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str, data_dir: str = "data") -> str:
    """
    将 DataFrame 保存为 CSV 文件
    
    Args:
        df: 要保存的数据
        filename: 文件名
        data_dir: 数据目录，默认为 "data"
    
    Returns:
        保存的文件路径
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)
    
    filepath = data_path / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"数据已保存到: {filepath}")
    return str(filepath)


if __name__ == "__main__":
    # 测试：抓取平安银行历史数据
    print("=" * 50)
    print("测试 A股历史数据抓取")
    print("=" * 50)
    
    df_hist = fetch_a_stock_hist(
        symbol="000001",
        period="daily",
        start_date="20240101",
        end_date="20240131"
    )
    
    if not df_hist.empty:
        print("\n历史数据预览:")
        print(df_hist.head())
        save_to_csv(df_hist, "a_stock_000001_sample.csv")
    
    print("\n" + "=" * 50)
    print("测试 A股实时行情获取")
    print("=" * 50)
    
    df_realtime = fetch_a_stock_realtime()
    if not df_realtime.empty:
        print("\n实时行情预览 (前5条):")
        print(df_realtime.head())
    
    print("\n测试完成!")
