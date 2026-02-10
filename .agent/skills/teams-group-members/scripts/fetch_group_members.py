"""
Teams群组成员查询脚本
从360teams平台获取指定群组的成员列表并解析详细信息

敏感配置通过 .env 文件加载：
- TEAMS_AUTHORIZATION: 授权令牌
"""
import os
import json
import argparse
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent.parent.parent.parent / '.env')

TEAMS_AUTHORIZATION = os.getenv('TEAMS_AUTHORIZATION')


def _check_env():
    """检查必需的环境变量是否已配置"""
    if not TEAMS_AUTHORIZATION:
        raise EnvironmentError("缺少必需的环境变量: TEAMS_AUTHORIZATION，请在 .env 文件中配置")


def _parse_extra(extra_str: str) -> dict:
    """
    解析成员记录中 extra 字段的嵌套 JSON 字符串

    Args:
        extra_str: extra 字段的 JSON 字符串

    Returns:
        解析后的字典，解析失败返回空字典
    """
    if not extra_str:
        return {}
    try:
        return json.loads(extra_str)
    except (json.JSONDecodeError, TypeError):
        return {}


def _parse_member(member: dict) -> dict:
    """
    将原始 API 成员记录解析为扁平化的字典

    Args:
        member: API 返回的单个成员原始数据

    Returns:
        包含完整成员信息的扁平化字典
    """
    extra = _parse_extra(member.get('extra', ''))
    return {
        'name': member.get('name', ''),
        'id': member.get('id', ''),
        'userName': extra.get('userName', ''),
        'role': member.get('role', 0),
        'role_desc': '群主' if member.get('role') == 1 else '普通成员',
        'deptName': extra.get('deptName', ''),
        'deptCode': extra.get('deptCode', ''),
        'superior': extra.get('superior', ''),
        'bpName': extra.get('bpName', ''),
        'workPlaceName': extra.get('workPlaceName', ''),
        'workPlaceCode': extra.get('workPlaceCode', ''),
        'sex': extra.get('sex', 0),
        'sex_desc': '女' if extra.get('sex') == 1 else '男',
        'portrait_url': member.get('portrait_url', ''),
        'create_dt': member.get('create_dt', 0),
        'gorder': member.get('gorder', 0),
    }


def fetch_group_members(
    group_code: str,
    authorization: Optional[str] = None,
    verbose: bool = True
) -> list[dict]:
    """
    获取指定群组的成员列表并解析详细信息

    Args:
        group_code: 群组代码，如 'FhSnheH3T_grT5yzxqVS5o'
        authorization: 授权令牌（可选，默认从环境变量读取）
        verbose: 是否打印结果信息

    Returns:
        解析后的成员信息字典列表，每个字典包含：
        - name: 姓名
        - id: 员工工号
        - userName: 登录账号
        - role: 角色编码 (1=群主, 4=普通成员)
        - role_desc: 角色描述
        - deptName: 部门名称
        - deptCode: 部门编码
        - superior: 直属上级
        - bpName: 对应BP
        - workPlaceName: 办公地点
        - workPlaceCode: 办公地点编码
        - sex: 性别编码 (0=男, 1=女)
        - sex_desc: 性别描述
        - portrait_url: 头像链接
        - create_dt: 加入群组时间戳（毫秒）
        - gorder: 群组内排序
    """
    authorization = authorization or TEAMS_AUTHORIZATION

    if not authorization:
        _check_env()

    url = f"https://im.360teams.com/api/qfin-api/rce-app/app/groups/members/{group_code}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": authorization,
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "*/*",
    }

    try:
        resp = requests.get(url, headers=headers)
        data = resp.json()
    except Exception as e:
        print(f"请求失败: {e}")
        return []

    if not resp.ok or data.get('code') != 0:
        print(f"请求失败: {data if resp.ok else resp.status_code}")
        return []

    raw_members = data.get('data', [])
    if not raw_members:
        print(f"群组 {group_code} 无成员数据")
        return []

    members = [_parse_member(m) for m in raw_members]

    if verbose:
        total = data.get('total', len(members))
        print(f"群组 {group_code} 共 {total} 名成员：")
        print(f"{'序号':<4} {'姓名':<8} {'工号':<14} {'部门':<16} {'上级':<8} {'工位':<20}")
        print("-" * 70)
        for i, m in enumerate(members, 1):
            print(f"{i:<4} {m['name']:<8} {m['id']:<14} {m['deptName']:<16} {m['superior']:<8} {m['workPlaceName']:<20}")

    return members


def main():
    """CLI入口"""
    _check_env()

    parser = argparse.ArgumentParser(description='获取360Teams群组成员信息')
    parser.add_argument('--group', '-g', type=str, required=True,
                        help='群组代码，如 FhSnheH3T_grT5yzxqVS5o')
    args = parser.parse_args()

    fetch_group_members(args.group)


if __name__ == '__main__':
    main()
