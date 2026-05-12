"""
小红书登录状态检测模块

集中管理登录检测逻辑，供 login_xhs.py 和 fetch_xhs.py 共用。

检测策略（按优先级）：
1. URL 检测：是否跳转到登录页
2. 元素检测：是否存在登录弹窗（遮罩层 + 登录框组合）
3. 内容验证：是否能看到搜索结果卡片
"""

import logging
from typing import Optional

from playwright.sync_api import Page, TimeoutError as PwTimeout

# 设置日志
logger = logging.getLogger(__name__)


class XHSAuth:
    """小红书登录状态检测器"""

    # 选择器常量（与 xhs_selectors.py 保持一致）
    LOGIN_MODAL = ".login-container"
    LOGIN_OVERLAY = ".login-vdiceas"
    LOGIN_MODAL_TITLE = ".login-container .title"
    QR_CODE_IMAGE = ".qrcode-img"
    LOGIN_BUTTON_TEXT = "登录"
    POST_CARD = "section.note-item"

    @staticmethod
    def _safe_visible(locator) -> bool:
        """安全检测元素是否可见"""
        try:
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    @classmethod
    def is_logged_in(cls, page: Page, check_url: str = None, debug: bool = False) -> bool:
        """
        检测是否已登录小红书

        Args:
            page: Playwright Page 对象
            check_url: 检测用的 URL，默认使用搜索页面
            debug: 是否输出调试信息

        Returns:
            bool: True 表示已登录，False 表示需要登录
        """
        check_url = check_url or "https://www.xiaohongshu.com/search_result?keyword=test"

        try:
            page.goto(check_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            if debug:
                print(f"[DEBUG] is_logged_in - URL: {page.url}", flush=True)

            # 1. URL 检测：如果跳转到登录页
            if "login" in page.url.lower():
                if debug:
                    print("[DEBUG] is_logged_in - 检测到登录页 URL，未登录", flush=True)
                logger.debug("检测到登录页 URL，未登录")
                return False

            # 2. 检测强制登录弹窗：遮罩层 + 登录弹窗同时出现
            login_modal = page.locator(cls.LOGIN_MODAL)
            overlay = page.locator(cls.LOGIN_OVERLAY)
            login_title = page.locator(cls.LOGIN_MODAL_TITLE)

            modal_visible = cls._safe_visible(login_modal)
            overlay_visible = cls._safe_visible(overlay)

            if debug:
                print(f"[DEBUG] is_logged_in - 弹窗: {modal_visible}, 遮罩: {overlay_visible}", flush=True)

            if modal_visible and overlay_visible:
                if debug:
                    print("[DEBUG] is_logged_in - 检测到登录弹窗 + 遮罩层，未登录", flush=True)
                logger.debug("检测到登录弹窗 + 遮罩层，未登录")
                return False

            # 3. 备用检测：登录弹窗内有明显的"登录"标题且可见
            if modal_visible and cls._safe_visible(login_title):
                if debug:
                    print("[DEBUG] is_logged_in - 检测到登录弹窗标题，未登录", flush=True)
                logger.debug("检测到登录弹窗标题，未登录")
                return False

            # 4. 检测二维码（不一定是未登录，但结合其他条件判断）
            qr_code = page.locator(cls.QR_CODE_IMAGE)
            login_btn = page.locator(f"text={cls.LOGIN_BUTTON_TEXT}")

            if cls._safe_visible(qr_code) and cls._safe_visible(login_btn):
                if debug:
                    print("[DEBUG] is_logged_in - 检测到二维码 + 登录按钮，未登录", flush=True)
                logger.debug("检测到二维码 + 登录按钮，未登录")
                return False

            # 5. 必须验证搜索结果卡片存在，才算登录成功
            post_cards = page.locator(cls.POST_CARD)
            card_count = post_cards.count()
            if debug:
                print(f"[DEBUG] is_logged_in - 搜索结果卡片数量: {card_count}", flush=True)

            if card_count > 0:
                if debug:
                    print("[DEBUG] is_logged_in - 检测到搜索结果卡片，已登录", flush=True)
                logger.debug("检测到搜索结果卡片，已登录")
                return True

            # 无卡片，可能是网络问题或未登录
            if debug:
                print("[DEBUG] is_logged_in - 未检测到搜索结果卡片，未登录", flush=True)
            logger.debug("未检测到搜索结果卡片")
            return False

        except Exception as e:
            if debug:
                print(f"[DEBUG] is_logged_in - 异常: {e}", flush=True)
            logger.warning(f"登录检测异常: {e}")
            return False

    @classmethod
    def is_not_logged_in(cls, page: Page, debug: bool = False) -> bool:
        """
        检测是否处于未登录状态（需要强制登录才能继续）

        注意：小红书页面经常会有"扫码关注作者"、"扫码下载APP"等二维码，
        以及"登录后关注"等按钮，这些并不意味着用户未登录。
        只有出现遮罩层 + 登录弹窗的组合，才是真正的强制登录状态。

        Args:
            page: Playwright Page 对象
            debug: 是否输出调试信息

        Returns:
            bool: True 表示需要登录，False 表示已登录或不确定
        """
        # 1. URL 检测：如果跳转到登录页，说明需要登录
        if "login" in page.url.lower():
            if debug:
                print(f"[DEBUG] URL 包含 login: {page.url}", flush=True)
            return True

        try:
            # 等待页面稳定（增加等待时间）
            page.wait_for_timeout(3000)

            # 2. 检测搜索结果卡片：如果能看到卡片，说明已登录
            post_cards = page.locator(cls.POST_CARD)
            card_count = post_cards.count()
            if debug:
                print(f"[DEBUG] 搜索结果卡片数量: {card_count}", flush=True)

            if card_count > 0:
                logger.debug("检测到搜索结果卡片，已登录")
                return False

            # 3. 检测强制登录弹窗：必须同时出现遮罩层 + 登录弹窗
            # 这是强制登录的唯一可靠标志
            login_modal = page.locator(cls.LOGIN_MODAL)
            overlay = page.locator(cls.LOGIN_OVERLAY)

            modal_visible = cls._safe_visible(login_modal)
            overlay_visible = cls._safe_visible(overlay)

            if debug:
                print(f"[DEBUG] 登录弹窗可见: {modal_visible}, 遮罩层可见: {overlay_visible}", flush=True)

            # 只有遮罩层 + 弹窗同时出现才是强制登录
            if modal_visible and overlay_visible:
                # 确认：等待 1 秒后再次检测，避免页面加载时的短暂闪现
                page.wait_for_timeout(1000)
                modal_visible = cls._safe_visible(login_modal)
                overlay_visible = cls._safe_visible(overlay)
                card_count = post_cards.count()
                if debug:
                    print(f"[DEBUG] 二次确认 - 弹窗: {modal_visible}, 遮罩: {overlay_visible}, 卡片: {card_count}", flush=True)
                if modal_visible and overlay_visible:
                    # 最后再检查一次卡片，可能是加载慢
                    if card_count > 0:
                        return False
                    return True

            # 4. 如果没有遮罩层但有弹窗，等待更长时间看卡片是否会加载
            if modal_visible and not overlay_visible:
                if debug:
                    print(f"[DEBUG] 弹窗可见但无遮罩层，等待卡片加载...", flush=True)
                # 等待卡片加载
                for i in range(3):
                    page.wait_for_timeout(2000)
                    card_count = post_cards.count()
                    if debug:
                        print(f"[DEBUG] 等待 {i+1} 次后卡片数量: {card_count}", flush=True)
                    if card_count > 0:
                        return False

                # 卡片仍然没有，但弹窗可见且无遮罩层
                # 这种情况可能是风控或网络问题，不一定是强制登录
                if debug:
                    print(f"[DEBUG] 卡片未加载，可能是风控或网络问题", flush=True)
                return False  # 不判定为强制登录

        except Exception as e:
            logger.debug(f"登录状态检测异常: {e}")
            if debug:
                print(f"[DEBUG] 异常: {e}", flush=True)

        return False

    @classmethod
    def wait_for_login(cls, page: Page, timeout: int = 120) -> bool:
        """
        等待用户完成扫码登录

        Args:
            page: Playwright Page 对象
            timeout: 超时秒数

        Returns:
            bool: True 表示登录成功，False 表示超时或失败
        """
        try:
            # 等待登录弹窗消失
            page.wait_for_selector(
                cls.LOGIN_MODAL,
                state="hidden",
                timeout=timeout * 1000
            )

            # 再次验证登录状态
            return cls.is_logged_in(page)

        except PwTimeout:
            logger.warning(f"等待登录超时 ({timeout}s)")
            return False
        except Exception as e:
            logger.error(f"等待登录异常: {e}")
            return False
