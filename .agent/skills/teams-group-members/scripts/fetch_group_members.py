"""
Teams群组成员查询脚本
从360teams平台获取指定群组的成员列表并解析详细信息

敏感配置通过 .env 文件加载：
- TEAMS_AUTHORIZATION: 授权令牌
- TEAMS_GROUP_CODES: 固定群组列表（逗号分隔）
"""
import os
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

try:
    from .generate_org_tree_html import render_org_tree_html
except ImportError:
    from generate_org_tree_html import render_org_tree_html

# 加载环境变量
load_dotenv(Path(__file__).parent.parent.parent.parent.parent / '.env')

TEAMS_AUTHORIZATION = os.getenv('TEAMS_AUTHORIZATION')
TEAMS_GROUP_CODES = os.getenv('TEAMS_GROUP_CODES', '')
DEFAULT_LATEST_HTML_PATH = 'data/latest_group_members_org_tree.html'


def _check_env(authorization: Optional[str] = None):
    """检查必需的环境变量是否已配置"""
    if not (authorization or TEAMS_AUTHORIZATION):
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


def _parse_group_codes(group_codes_str: Optional[str] = None) -> list[str]:
    """
    解析群组代码列表字符串

    Args:
        group_codes_str: 逗号分隔的群组代码字符串，未传时默认读取环境变量

    Returns:
        清洗后的群组代码列表
    """
    raw = TEAMS_GROUP_CODES if group_codes_str is None else group_codes_str
    return [code.strip() for code in raw.split(',') if code and code.strip()]


def _member_unique_key(member: dict) -> Optional[str]:
    """
    构造成员去重键，优先 id，回退 userName
    """
    member_id = str(member.get('id', '')).strip()
    if member_id:
        return f"id:{member_id}"

    user_name = str(member.get('userName', '')).strip()
    if user_name:
        return f"userName:{user_name}"

    return None


def _dedupe_members(members: list[dict]) -> list[dict]:
    """
    对成员列表去重：优先按 id，id 为空时按 userName
    """
    seen = set()
    deduped = []
    for member in members:
        key = _member_unique_key(member)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        deduped.append(member)
    return deduped


def _append_virtual_superiors(members: list[dict]) -> list[dict]:
    """
    若成员 superior 不在当前成员 name 中，则创建同名虚拟上级节点（同名合并）
    """
    existing_names = {str(m.get('name', '')).strip() for m in members if str(m.get('name', '')).strip()}
    virtual_names = {
        str(m.get('name', '')).strip()
        for m in members
        if m.get('is_virtual') and str(m.get('name', '')).strip()
    }

    missing_superiors = []
    for m in members:
        superior = str(m.get('superior', '')).strip()
        if not superior:
            continue
        if superior in existing_names or superior in virtual_names:
            continue
        missing_superiors.append(superior)

    unique_missing = sorted(set(missing_superiors))
    if not unique_missing:
        return members

    virtual_members = []
    for idx, superior_name in enumerate(unique_missing, 1):
        virtual_members.append(
            {
                'name': superior_name,
                'id': f'VIRTUAL_SUPERIOR_{idx}',
                'userName': '',
                'role': 0,
                'role_desc': '虚拟上级',
                'deptName': '虚拟上级',
                'deptCode': '',
                'superior': '',
                'bpName': '',
                'workPlaceName': '',
                'workPlaceCode': '',
                'sex': 0,
                'sex_desc': '未知',
                'portrait_url': '',
                'create_dt': 0,
                'gorder': 0,
                'is_virtual': True,
            }
        )

    return members + virtual_members


def _save_members(members: list[dict], save_path: str):
    """
    保存成员列表到 JSON 文件
    """
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        json.dump(members, f, ensure_ascii=False, indent=2)
    print(f"成员数据已保存: {path.as_posix()}")


def _resolve_html_path(save_path: Optional[str] = None) -> str:
    """
    计算组织树 HTML 输出路径
    """
    if not save_path:
        return DEFAULT_LATEST_HTML_PATH

    json_path = Path(save_path)
    stem = json_path.stem if json_path.suffix else json_path.name
    return (json_path.parent / f"{stem}_org_tree.html").as_posix()


def fetch_group_members(
    group_code: str,
    authorization: Optional[str] = None,
    verbose: bool = True,
    save_path: Optional[str] = None,
    fill_virtual_superiors: bool = True,
    generate_html: bool = True
) -> list[dict]:
    """
    获取指定群组的成员列表并解析详细信息

    Args:
        group_code: 群组代码，如 'FhSnheH3T_grT5yzxqVS5o'
        authorization: 授权令牌（可选，默认从环境变量读取）
        verbose: 是否打印结果信息
        save_path: 保存路径（可选），传入时保存为 JSON
        fill_virtual_superiors: 是否补齐虚拟上级节点，默认 True
        generate_html: 是否在抓取后生成组织树 HTML，默认 True

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
        _check_env(authorization)

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

    if fill_virtual_superiors:
        members = _append_virtual_superiors(members)

    if verbose:
        total = len(members)
        print(f"群组 {group_code} 共 {total} 名成员：")
        print(f"{'序号':<4} {'姓名':<8} {'工号':<14} {'部门':<16} {'上级':<8} {'工位':<20}")
        print("-" * 70)
        for i, m in enumerate(members, 1):
            print(f"{i:<4} {m['name']:<8} {m['id']:<14} {m['deptName']:<16} {m['superior']:<8} {m['workPlaceName']:<20}")

    if save_path:
        _save_members(members, save_path)

    if generate_html:
        html_out = render_org_tree_html(
            members=members,
            output_path=_resolve_html_path(save_path),
            fetched_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        print(f"组织架构树 HTML 已保存: {html_out}")

    return members


def fetch_group_members_union(
    group_codes: list[str],
    authorization: Optional[str] = None,
    verbose: bool = True,
    save_path: Optional[str] = None,
    generate_html: bool = True
) -> list[dict]:
    """
    批量抓取多个群组成员，合并并去重后返回

    Args:
        group_codes: 群组代码列表
        authorization: 授权令牌（可选，默认从环境变量读取）
        verbose: 是否打印过程信息
        save_path: 保存路径（可选），传入时保存为 JSON
        generate_html: 是否在抓取后生成组织树 HTML，默认 True
    """
    authorization = authorization or TEAMS_AUTHORIZATION
    if not authorization:
        _check_env(authorization)

    clean_group_codes = [code.strip() for code in group_codes if code and code.strip()]
    if not clean_group_codes:
        raise ValueError("群组列表为空，请检查 TEAMS_GROUP_CODES 或传入参数")

    if verbose:
        print(f"开始批量抓取，共 {len(clean_group_codes)} 个群组")

    all_members = []
    for idx, group_code in enumerate(clean_group_codes, 1):
        if verbose:
            print(f"[{idx}/{len(clean_group_codes)}] 抓取群组: {group_code}")
        group_members = fetch_group_members(
            group_code=group_code,
            authorization=authorization,
            verbose=False,
            fill_virtual_superiors=False,
            generate_html=False,
        )
        all_members.extend(group_members)
        if verbose:
            print(f"群组 {group_code} 获取 {len(group_members)} 名成员")

    deduped_members = _dedupe_members(all_members)
    deduped_members = _append_virtual_superiors(deduped_members)
    if verbose:
        print(f"批量抓取完成，原始记录 {len(all_members)} 条，去重后 {len(deduped_members)} 条")

    if save_path:
        _save_members(deduped_members, save_path)

    if generate_html:
        html_out = render_org_tree_html(
            members=deduped_members,
            output_path=_resolve_html_path(save_path),
            fetched_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
        print(f"组织架构树 HTML 已保存: {html_out}")

    return deduped_members


def main():
    """CLI入口"""
    _check_env()

    parser = argparse.ArgumentParser(description='获取360Teams群组成员信息')
    parser.add_argument('--group', '-g', type=str,
                        help='单个群组代码，如 FhSnheH3T_grT5yzxqVS5o')
    parser.add_argument('--output', '-o', type=str,
                        help='输出文件路径（JSON），如 data/members.json')
    args = parser.parse_args()

    if args.group:
        fetch_group_members(args.group, save_path=args.output)
        return

    group_codes = _parse_group_codes()
    if not group_codes:
        raise EnvironmentError(
            "未指定 --group 且缺少 TEAMS_GROUP_CODES，请在 .env 配置逗号分隔群组列表"
        )

    fetch_group_members_union(group_codes, save_path=args.output)


if __name__ == '__main__':
    main()
