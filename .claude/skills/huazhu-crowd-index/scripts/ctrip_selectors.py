"""
携程（Ctrip）酒店页面选择器集中模块。

DOM 实测核对日期：2026-06-05（通过 _calibrate*.py 在真机登录态下验证）。
携程前端 class 多为哈希化，但本文件所用选择器均为实测稳定项：
  - 酒店名 span.hotelName
  - 列表卡片 .right-card（含酒店名 + 价格 + 售罄文案）
  - 售价 .sale（实际可订价；.delete 为划线原价）
若日后失效，用 _calibrate_card.py 重新核对后更新此处。
"""


class CtripSelectors:
    HOME_URL = "https://hotels.ctrip.com/"

    # 列表页 URL 模板：只需 cityId + 入住/退房日期即可直达（无需操作日历）
    LIST_URL_TEMPLATE = (
        "https://hotels.ctrip.com/hotels/list?flexType=1"
        "&cityId={city_id}&countryId=1&searchType=CT&optionId={city_id}"
        "&checkin={checkin}&checkout={checkout}&crn=1&curr=CNY&locale=zh-CN"
    )

    # ---- 登录态判定 ----
    # 首页头部「登录」按钮 class 含 home_header_login_not；登录后该元素消失。
    LOGOUT_MARKER = "[class*='home_header_login_not']"

    # ---- 首页/列表页搜索表单 ----
    DESTINATION_INPUT = "#destinationInput"           # 目的地（解析 cityId 时用）
    # 列表页顶部「位置/品牌/酒店(选填)」框：输入「汉庭」+ 搜索即按品牌过滤列表。
    # 注意：该框仅在 ≥1920 宽视口下渲染（窄屏折叠成全局搜索框）。
    BRAND_INPUT = "input[placeholder*='品牌']"
    SEARCH_BUTTON = ["button:has-text('搜索')", "[class*='searchBtn']", "text=搜索"]

    # ---- 列表页：酒店卡片 ----
    HOTEL_CARD = ".right-card"      # 每家酒店一个，含名称+价格+售罄
    HOTEL_NAME = "span.hotelName"   # 酒店名
    HOTEL_PRICE = ".sale"           # 实际可订最低价（.delete 是划线原价，忽略）
    ROOM_TYPE = ".room-name"        # 房型名（列表卡片可能不展示，取不到留空）

    # 售罄 / 无房文案（出现在卡片文本中即判售罄）
    SOLD_OUT_TEXTS = ["已订完", "订完", "无房", "售罄", "满房", "暂无报价"]

    # 酒店名定位到所在卡片的 XPath（兜底：祖先里含 ¥ 价格的最近节点）
    CARD_FROM_NAME_XPATH = "xpath=ancestor::*[contains(@class,'right-card')][1]"
    CARD_FROM_NAME_XPATH_FALLBACK = "xpath=ancestor::*[.//*[contains(text(),'¥')]][1]"
