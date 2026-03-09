"""
小红书登录脚本
独立负责登录状态检查、二维码登录和 Cookie 持久化。
"""

import argparse
import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright

# 导入同目录下的选择器
from xhs_selectors import XHSSelectors as S

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()


class XHSLogin:
    def __init__(self):
        # 强制有头模式：在无 DISPLAY 时报错退出
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            print("[✗] 检测到无 DISPLAY 环境变量", file=sys.stderr, flush=True)
            print("    请先启动虚拟显示器:", file=sys.stderr, flush=True)
            print("    Xvfb :99 -screen 0 1920x1080x24 &", file=sys.stderr, flush=True)
            print("    export DISPLAY=:99", file=sys.stderr, flush=True)
            sys.exit(1)

        self.auth_state_path = os.environ.get(
            "XHS_AUTH_STATE",
            ".claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json",
        )
        Path(self.auth_state_path).parent.mkdir(parents=True, exist_ok=True)
        self.qr_path = str((Path.cwd() / "xhs_qr_login.png").resolve())

    def _build_context(self, browser):
        if os.path.exists(self.auth_state_path):
            try:
                return browser.new_context(storage_state=self.auth_state_path)
            except Exception:
                return browser.new_context()
        return browser.new_context()

    @staticmethod
    def _safe_visible(locator):
        try:
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    def _is_logged_in(self, page) -> bool:
        # 检测搜索页面而非 explore 页面，因为搜索页面有更严格的登录要求
        page.goto("https://www.xiaohongshu.com/search_result?keyword=test", wait_until="domcontentloaded")
        try:
            # 等待页面加载
            page.wait_for_timeout(2000)
            # 检查是否有登录模态框或二维码
            login_modal = page.locator(S.LOGIN_MODAL)
            qr_code = page.locator(S.QR_CODE_IMAGE)
            login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")

            # 如果出现任何登录元素，说明未登录
            if self._safe_visible(login_modal) or self._safe_visible(qr_code) or self._safe_visible(login_btn):
                return False
            return True
        except Exception:
            return False

    def _cleanup_qr(self):
        if os.path.exists(self.qr_path):
            os.remove(self.qr_path)

    def run(self, check_only: bool, timeout: int) -> int:
        with sync_playwright() as pw:
            launch_kw = {"headless": False}
            if sys.platform == "win32":
                launch_kw["channel"] = "msedge"

            browser = pw.chromium.launch(**launch_kw)
            ctx = self._build_context(browser)
            page = ctx.new_page()

            try:
                if self._is_logged_in(page):
                    print("LOGIN_OK")
                    return 0

                if check_only:
                    print(f"NEED_LOGIN:{self.qr_path}")
                    return 1

                login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
                if self._safe_visible(login_btn):
                    login_btn.first.click()

                page.wait_for_selector(S.QR_CODE_IMAGE, state="visible", timeout=15000)
                modal = page.locator(S.LOGIN_MODAL)
                modal.screenshot(path=self.qr_path)
                print(f"NEED_LOGIN:{self.qr_path}")

                page.wait_for_selector(S.LOGIN_MODAL, state="hidden", timeout=timeout * 1000)
                if not self._is_logged_in(page):
                    print("LOGIN_FAILED")
                    return 1

                ctx.storage_state(path=self.auth_state_path)
                self._cleanup_qr()
                print("LOGIN_SUCCESS")
                return 0
            except PwTimeout:
                self._cleanup_qr()
                print("LOGIN_TIMEOUT")
                return 2
            except Exception:
                self._cleanup_qr()
                print("LOGIN_FAILED")
                return 1
            finally:
                ctx.close()
                browser.close()


def main():
    parser = argparse.ArgumentParser(description="小红书登录工具")
    parser.add_argument("--check-only", action="store_true", help="仅检查 Cookie 是否有效")
    parser.add_argument("--timeout", type=int, default=120, help="扫码等待超时秒数，默认 120")
    args = parser.parse_args()

    login = XHSLogin()
    code = login.run(check_only=args.check_only, timeout=args.timeout)
    sys.exit(code)


if __name__ == "__main__":
    main()
