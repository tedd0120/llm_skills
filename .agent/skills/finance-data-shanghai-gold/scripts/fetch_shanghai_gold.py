"""
沪金数据抓取模块
使用 akshare 库获取上海黄金交易所数据
"""

import akshare as ak
import pandas as pd
from pathlib import Path
from typing import List


def get_sge_symbols() -> List[str]:
    """
    获取上海黄金交易所支持的品种列表
    
    Returns:
        品种代码列表
    """
    return [
        "Au9999",   # 黄金9999
        "Au9995",   # 黄金9995
        "Au100g",   # 100克黄金
        "mAu",      # 迷你黄金
        "Au(T+D)",  # 黄金T+D
        "Ag(T+D)",  # 白银T+D
        "Ag9999",   # 白银9999
    ]


def fetch_sge_gold_hist(symbol: str = "Au9999") -> pd.DataFrame:
    """
    获取上海黄金交易所黄金现货历史数据
    
    Args:
        symbol: 品种代码，如 "Au9999", "Au9995", "Au100g"
    
    Returns:
        DataFrame 包含历史行情数据
    """
    try:
        df = ak.spot_hist_sge(symbol=symbol)
        print(f"成功获取沪金 {symbol} 的历史数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"获取沪金数据失败: {e}")
        return pd.DataFrame()


def fetch_sge_realtime() -> pd.DataFrame:
    """
    获取上海黄金交易所实时行情
    
    Returns:
        DataFrame 包含实时行情
    """
    try:
        df = ak.spot_symbol_table_sge()
        print(f"成功获取沪金实时行情")
        return df
    except Exception as e:
        print(f"获取沪金实时行情失败: {e}")
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
    # 显示支持的品种
    print("=" * 50)
    print("上海黄金交易所支持的品种")
    print("=" * 50)
    print(get_sge_symbols())
    
    # 测试：抓取 Au9999 历史数据
    print("\n" + "=" * 50)
    print("测试 沪金历史数据抓取")
    print("=" * 50)
    
    df_hist = fetch_sge_gold_hist(symbol="Au9999")
    if not df_hist.empty:
        print("\n历史数据预览:")
        print(df_hist.head())
        save_to_csv(df_hist, "sge_au9999_sample.csv")
    
    print("\n测试完成!")
