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

def print_statistics(today: str, att_df: pd.DataFrame, check_month: str) -> None:
    """
    格式化输出考勤统计信息

    Args:
        today: 当前日期 (YYYY-MM-DD)
        att_df: 考勤明细 DataFrame
        check_month: 查询月份 (YYYY-MM)
    """
    # 计算已工作天数（不包含今天，使用有效工作日字段）
    past_data = att_df[att_df['日期'] < today]
    worked_days = past_data['有效工作日'].sum()

    # 计算已累计工时（不包含今天）
    worked_hours = past_data['工时'].sum()

    # 计算当前平均工时
    avg_hours = round(worked_hours / worked_days, 2) if worked_days > 0 else 0

    # 计算剩余工作日（本月范围内，日期 >= today 且 isrest=0）
    month_data = att_df[att_df['月份'] == check_month]
    remaining_days = month_data[(month_data['日期'] >= today) & (month_data['假期flag'] == 0)].shape[0]

    # 无数据情况
    if att_df.empty:
        print("暂无本月考勤数据")
        return

    # 输出基础统计表格
    border = "═" * 57
    print(f"\n{border}")
    print(f"  考勤统计 - {check_month}")
    print(border)
    print(f"  当前日期         {today}")
    print(f"  已工作天数       {worked_days} 天")
    print(f"  已累计工时       {worked_hours} 小时")
    print(f"  当前平均工时     {avg_hours} 小时/天")
    print()

    # 输出达标预测表格（如果有剩余工作日）
    if remaining_days > 0:
        print(f"  剩余工作日       {remaining_days} 天")
        print()
        # 硬编码目标工时
        targets = [10.5, 10.7, 11.0]
        total_work_days = worked_days + remaining_days

        print("┌────────────┬──────────────┐")
        print("│  目标工时   │  剩余日均需  │")
        print("├────────────┼──────────────┤")

        for target in targets:
            target_total = target * total_work_days
            remaining_needed = target_total - worked_hours
            daily_needed = round(remaining_needed / remaining_days, 1) if remaining_days > 0 else 0
            print(f"│   {target:4.1f} h   │   {daily_needed:6.1f} h   │")

        print("└────────────┴──────────────┘")
    else:
        print("本月已结束")

    # 输出本月明细表
    _print_detail_table(today, att_df, check_month)

    print()  # 空行分隔


def _print_detail_table(today: str, att_df: pd.DataFrame, check_month: str) -> None:
    """
    输出本月工作日明细表

    Args:
        today: 当前日期 (YYYY-MM-DD)
        att_df: 考勤明细 DataFrame
        check_month: 查询月份 (YYYY-MM)
    """
    # 过滤数据：本月 + 排除今天 + 排除节假日
    detail_df = att_df[
        (att_df['月份'] == check_month) &
        (att_df['日期'] < today) &
        (att_df['假期flag'] == 0)
    ].copy()

    if detail_df.empty:
        return

    # 格式化数据
    detail_df['日期简写'] = detail_df['日期'].str[5:]  # 2026-03-02 -> 03-02
    # 时间格式: 2026-03-02 09:14:09 -> 09:14
    detail_df['上班简写'] = detail_df['上班打卡'].str[11:16]
    detail_df['下班简写'] = detail_df['下班打卡'].str[11:16]
    detail_df['工时格式'] = detail_df['工时'].apply(lambda x: f"{x:.2f}h")

    # 输出表格
    border = "━" * 57
    print(f"\n{border}")
    print("  本月明细")
    print(border)
    print()

    print("│  日期   │ 上班时间 │ 下班时间 │  工时   │  备注  │")
    print("│---------│----------│----------│---------│---------│")

    for _, row in detail_df.iterrows():
        date_str = row['日期简写']
        start_time = row['上班简写']
        end_time = row['下班简写']
        hours = row['工时格式']
        note = row['备注'] if pd.notna(row['备注']) and row['备注'] else ''

        print(f"│ {date_str}   │ {start_time}    │ {end_time}    │ {hours}  │ {note:<6s} │")

    # 汇总信息
    total_days = len(detail_df)
    total_hours = detail_df['工时'].sum()

    print()
    print(f"共 {total_days} 个工作日，累计 {total_hours:.2f} 小时")

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

def parsed_att_date(check_month: str, em_code: Optional[str] = None, authorization: Optional[str] = None, output_path: Optional[str] = None):
    """
    获取指定月份的考勤明细和统计

    Args:
        check_month: 查询月份，格式 YYYY-MM
        em_code: 员工编码（可选，默认从环境变量读取）
        authorization: 授权令牌（可选，默认从环境变量读取）
        output_path: CSV输出路径（可选，默认为 data/attendance_YYYYMM.csv）

    Returns:
        [平均工时, 考勤明细DataFrame]

    注意：输出格式固定，不可更改。统计信息始终以固定格式打印到终端。
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

    # 按日期去重，保留第一条记录（同一日期可能有多条备注记录）
    att_df = att_df[att_df['月份'] == check_month].drop_duplicates(subset=['日期']).reset_index(drop=True)

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

    # 输出统计信息（固定格式，始终输出）
    print_statistics(today, att_df, check_month)

    # 强制保存 CSV（默认路径或用户指定路径）
    save_path = output_path or f"data/attendance_{check_month.replace('-', '')}.csv"
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    att_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"考勤明细已保存至: {save_path}")

    return [avg_hours, att_df]


def main():
    """CLI入口"""
    _check_env()

    # 默认查询当前月份
    default_month = pd.Timestamp.now().strftime("%Y-%m")

    parser = argparse.ArgumentParser(description='获取Teams考勤数据并计算工时统计')
    parser.add_argument('--month', '-m', type=str,
                        default=default_month,
                        help='查询月份，格式 YYYY-MM，默认为当前月份')
    parser.add_argument('--output', '-o', type=str,
                        default=f"data/attendance_{default_month.replace('-', '')}.csv",
                        help='CSV输出路径，默认为 data/attendance_YYYYMM.csv')
    args = parser.parse_args()

    parsed_att_date(args.month, output_path=args.output)


if __name__ == '__main__':
    main()
