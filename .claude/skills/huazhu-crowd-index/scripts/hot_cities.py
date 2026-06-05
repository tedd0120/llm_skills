"""
华住人流量指数 - 内置默认数据

包含两部分：
1. HOT_CITIES   —— 全国热门城市默认清单（用户运行时可覆盖）
2. HUAZHU_BRANDS —— 华住（H World）旗下主要品牌名，用于在携程结果里筛选/识别华住酒店

品牌清单核对日期：2026-06-05（华住官网品牌矩阵）。新增品牌时只需在此追加。
"""

# 默认对比城市（用户未指定时使用）。覆盖一二线 + 热门旅游城市。
HOT_CITIES = [
    "北京", "上海", "广州", "深圳",
    "杭州", "成都", "西安", "重庆",
    "南京", "武汉", "苏州", "长沙",
    "厦门", "青岛", "三亚", "丽江",
]

# 携程 cityId 种子表（2026-06-05 通过 UI 解析实测）。命中则免去动态解析，直接拼列表 URL。
# 未在表内的城市，fetch_prices.py 会用 UI 流程动态解析并复用。
CITY_IDS = {
    "北京": 1, "上海": 2, "广州": 32, "深圳": 30,
    "杭州": 17, "成都": 28, "西安": 10, "重庆": 4,
    "南京": 12, "武汉": 477, "苏州": 14, "长沙": 206,
    "厦门": 25, "青岛": 7, "三亚": 43, "丽江": 37,
}

# 华住旗下主要品牌（含经济型 / 中端 / 中高端 / 高端 / 生活方式）。
# 用于：①携程品牌筛选 ②酒店名包含其一即判定为华住系。
HUAZHU_BRANDS = [
    # 经济型
    "汉庭", "海友", "你好", "怡莱", "宜必思",
    # 中端
    "全季", "桔子", "桔子水晶", "星程", "智选假日", "美居", "诺富特",
    # 中高端 / 高端
    "美居", "美爵", "美仑", "施柏阁", "禧玥", "花间堂", "永乐半山",
    # 生活方式 / 其它
    "漫心", "CitiGO", "城际", "宜尚", "希岸", "兰欧", "麗枫", "喆啡", "starway",
]


def normalize_city(name: str) -> str:
    """去掉用户输入里常见的「市」后缀与空白，统一城市名。"""
    name = (name or "").strip()
    for suffix in ("市",):
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
    return name


def parse_cities(raw: str) -> list:
    """
    解析用户输入的城市清单。
    - 空 / None  -> 返回内置 HOT_CITIES 副本
    - 否则按逗号/中文逗号/空格/分号拆分，去重保序
    """
    if not raw or not raw.strip():
        return list(HOT_CITIES)

    import re
    parts = re.split(r"[,，;、\s]+", raw.strip())
    seen, out = set(), []
    for p in parts:
        c = normalize_city(p)
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out or list(HOT_CITIES)


def is_huazhu(hotel_name: str) -> str:
    """
    判断酒店名是否属于华住系；命中则返回品牌名，否则返回空字符串。
    优先匹配更长的品牌名（如「桔子水晶」先于「桔子」）。
    """
    name = (hotel_name or "")
    for brand in sorted(HUAZHU_BRANDS, key=len, reverse=True):
        if brand and brand.lower() in name.lower():
            return brand
    return ""


def is_hanting(hotel_name: str) -> bool:
    """
    判断酒店名是否为「汉庭」系（汉庭/汉庭优佳/汉庭3.5 等均含「汉庭」二字）。
    汉庭是华住最基础、每城必有的系列，用作跨城横向可比的锚点。
    """
    return "汉庭" in (hotel_name or "")
