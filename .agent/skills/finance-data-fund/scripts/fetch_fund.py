"""
基金数据抓取模块
使用 akshare 库获取公募基金和ETF数据
"""

import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime


def fetch_fund_nav(fund_code: str) -> pd.DataFrame:
    """
    获取开放式基金历史净值数据
    
    Args:
        fund_code: 基金代码，如 "005827"
    
    Returns:
        DataFrame 包含净值数据
    """
    try:
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        print(f"成功获取基金 {fund_code} 的净值数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取基金净值失败: {e}")
        return pd.DataFrame()


def fetch_etf_hist(
    symbol: str,
    period: str = "daily",
    start_date: str = None,
    end_date: str = None,
    adjust: str = "qfq"
) -> pd.DataFrame:
    """
    获取ETF历史行情数据
    
    Args:
        symbol: ETF代码，如 "510300"
        period: 周期，可选 "daily", "weekly", "monthly"
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
        df = ak.fund_etf_hist_em(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        print(f"成功获取 ETF {symbol} 的历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取ETF数据失败: {e}")
        return pd.DataFrame()


def fetch_fund_list() -> pd.DataFrame:
    """
    获取所有公募基金列表
    
    Returns:
        DataFrame 包含基金代码和名称
    """
    try:
        df = ak.fund_name_em()
        print(f"成功获取基金列表，共 {len(df)} 只基金")
        return df
    except Exception as e:
        print(f"获取基金列表失败: {e}")
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
    # 测试：抓取基金净值
    print("=" * 50)
    print("测试 基金净值数据抓取")
    print("=" * 50)
    
    df_nav = fetch_fund_nav(fund_code="005827")
    if not df_nav.empty:
        print("\n基金净值预览:")
        print(df_nav.head())
        save_to_csv(df_nav, "fund_005827_nav.csv")
    
    print("\n" + "=" * 50)
    print("测试 ETF历史数据抓取")
    print("=" * 50)
    
    df_etf = fetch_etf_hist(
        symbol="510300",
        start_date="20240101",
        end_date="20240131"
    )
    if not df_etf.empty:
        print("\nETF数据预览:")
        print(df_etf.head())
        save_to_csv(df_etf, "etf_510300_sample.csv")
    
    print("\n测试完成!")
