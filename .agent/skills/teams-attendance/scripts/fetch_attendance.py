"""
Teams考勤数据获取脚本
从360teams平台获取考勤数据并计算工时统计

敏感配置通过 .env 文件加载：
- TEAMS_EM_CODE: 员工编码
- TEAMS_AUTHORIZATION: 授权令牌
"""
import os
import argparse
import requests
import pandas as pd
import warnings
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

warnings.filterwarnings('ignore')

# 加载环境变量
load_dotenv(Path(__file__).parent.parent.parent.parent.parent / '.env')

TEAMS_EM_CODE = os.getenv('TEAMS_EM_CODE')
TEAMS_AUTHORIZATION = os.getenv('TEAMS_AUTHORIZATION')

def _check_env():
    """检查必需的环境变量是否已配置"""
    missing = []
    if not TEAMS_EM_CODE:
        missing.append('TEAMS_EM_CODE')
    if not TEAMS_AUTHORIZATION:
        missing.append('TEAMS_AUTHORIZATION')
    if missing:
        raise EnvironmentError(f"缺少必需的环境变量: {', '.join(missing)}，请在 .env 文件中配置")

def next_month(ym: str) -> str:
    """计算下一个月份"""
    return (pd.Period(ym, freq="M") + 1).strftime("%Y-%m")

def get_att_data(em_code: str, cycle: str, authorization: str) -> Optional[dict]:
    """
    获取指定月份的考勤数据
    
    Args:
        em_code: 员工编码
        cycle: 月份，格式 YYYY-MM
        authorization: 授权令牌
    
    Returns:
        API响应数据字典
    """
    url = "https://im.360teams.com/api/qfin-api/securityapi/attendance/query/detail"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "AppKey": "360teams",
        "Authorization": authorization,
    }
    resp = requests.get(url, headers=headers, params={"emCode": em_code, "attDate": "", "cycle": cycle})
    data = resp.json()
    if resp.ok and data.get('code') == 0:
        print(f"{cycle} 请求成功！")
        return data
    print(f"{cycle} 请求失败！{data if resp.ok else resp.status_code}")
    return None

def parsed_att_date(check_month: str, em_code: Optional[str] = None, authorization: Optional[str] = None, verbose: bool = True, output_path: Optional[str] = None):
    """
    获取指定月份的考勤明细和统计
    
    Args:
        check_month: 查询月份，格式 YYYY-MM
        em_code: 员工编码（可选，默认从环境变量读取）
        authorization: 授权令牌（可选，默认从环境变量读取）
        verbose: 是否打印统计信息
        output_path: CSV输出路径（可选，提供时保存明细到文件）
    
    Returns:
        [平均工时, 考勤明细DataFrame]
    """
    em_code = em_code or TEAMS_EM_CODE
    authorization = authorization or TEAMS_AUTHORIZATION
    
    if not em_code or not authorization:
        _check_env()
    
    # 获取数据
    data = []
    for m in [check_month, next_month(check_month)]:
        result = get_att_data(em_code, m, authorization)
        if result and result.get('data', {}).get('calendarList'):
            data += result['data']['calendarList']

    if not data:
        print(f"未获取到 {check_month} 的考勤数据")
        return [0, pd.DataFrame()]

    # 构建DataFrame
    att_df = pd.DataFrame([{
        '日期': d['attDate'],
        '月份': d['attDate'][:7],
        '假期flag': d['isrest'],
        '上班打卡': d['firstDate'],
        '下班打卡': d['endDate'],
        '备注': d['exp'],
        '备注2': d['resultList'][0] if d['resultList'] else None
    } for d in data])

    att_df = att_df[att_df['月份'] == check_month].drop_duplicates().reset_index(drop=True)

    att_df['工时'] = (pd.to_datetime(att_df['下班打卡']) - pd.to_datetime(att_df['上班打卡'])).dt.total_seconds() / 3600
    att_df.loc[att_df['假期flag'] != 0, '工时'] = 0

    # 计算有效工作日
    def calc_workday(s):
        if s['假期flag'] != 0:
            return 0
        if pd.isna(s['备注']) or s['备注'] in ['迟到', '早退']:
            return 1
        if s['备注'] in ['病假', '年假', '调休假']:
            return 0.5 if s['工时'] > 0 else 0
        return 0.5 if s['备注2'] and '半天' in s['备注2'] else 0

    att_df['有效工作日'] = att_df.apply(calc_workday, axis=1)

    # 统计
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    calc_data = att_df[att_df['日期'] < today]
    valid_days, valid_hours = calc_data['有效工作日'].sum(), calc_data['工时'].sum()
    avg_hours = round(valid_hours / valid_days, 2) if valid_days > 0 else 0

    if verbose:
        print(f"当前日期 {today} 检查月份 {check_month} 有效工作日 {valid_days} 有效工时 {round(valid_hours,2)} 平均工时 {avg_hours}")

    # 导出CSV
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        att_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"考勤明细已保存至: {output_path}")

    return [avg_hours, att_df]


def main():
    """CLI入口"""
    _check_env()
    
    parser = argparse.ArgumentParser(description='获取Teams考勤数据并计算工时统计')
    parser.add_argument('--month', '-m', type=str, 
                        default=pd.Timestamp.now().strftime("%Y-%m"),
                        help='查询月份，格式 YYYY-MM，默认为当前月份')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='CSV输出路径，不指定则不保存文件')
    args = parser.parse_args()
    
    parsed_att_date(args.month, verbose=True, output_path=args.output)


if __name__ == '__main__':
    main()
