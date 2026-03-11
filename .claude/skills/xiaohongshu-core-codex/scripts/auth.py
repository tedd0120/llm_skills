"""认证与登录共享能力（codex）。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PwTimeout
from playwright.sync_api import sync_playwright

from browser import build_launch_kwargs
from xhs_selectors import XHSSelectors as S

load_dotenv()


def get_auth_state_path() -> Path:
    script_dir = Path(__file__).parent.resolve()
    default_path = script_dir / "xhs_auth.json"
    auth_path = Path(os.environ.get("XHS_AUTH_STATE", str(default_path))).resolve()
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    return auth_path


def get_qr_path() -> Path:
    return (Path.cwd() / "xhs_qr_login.png").resolve()


class XHSAuthSession:
    def __init__(self):
        self.auth_state_path = get_auth_state_path()
        self.qr_path = get_qr_path()

    def _build_context(self, browser):
        if self.auth_state_path.exists():
            try:
                return browser.new_context(storage_state=str(self.auth_state_path))
            except Exception:
                return browser.new_context()
        return browser.new_context()

    @staticmethod
    def _safe_visible(locator) -> bool:
        try:
            return locator.count() > 0 and locator.first.is_visible()
        except Exception:
            return False

    def is_logged_in(self, page) -> bool:
        page.goto("https://www.xiaohongshu.com/search_result?keyword=test", wait_until="domcontentloaded")
        try:
            page.wait_for_timeout(2000)
            login_modal = page.locator(S.LOGIN_MODAL)
            qr_code = page.locator(S.QR_CODE_IMAGE)
            login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
            if self._safe_visible(login_modal) or self._safe_visible(qr_code) or self._safe_visible(login_btn):
                return False
            post_cards = page.locator(S.POST_CARD)
            return post_cards.count() > 0
        except Exception:
            return False

    def cleanup_qr(self) -> None:
        if self.qr_path.exists():
            self.qr_path.unlink()

    def ensure_login(self, timeout: int = 120) -> tuple[str, str | None]:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**build_launch_kwargs())
            ctx = self._build_context(browser)
            page = ctx.new_page()
            try:
                if self.is_logged_in(page):
                    ctx.storage_state(path=str(self.auth_state_path))
                    return "LOGIN_OK", None

                login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
                if self._safe_visible(login_btn):
                    login_btn.first.click()

                page.wait_for_selector(S.QR_CODE_IMAGE, state="visible", timeout=15000)
                page.locator(S.LOGIN_MODAL).screenshot(path=str(self.qr_path))
                print(f"NEED_LOGIN:{self.qr_path}", flush=True)
                page.wait_for_selector(S.LOGIN_MODAL, state="hidden", timeout=timeout * 1000)

                if not self.is_logged_in(page):
                    return "LOGIN_FAILED", None

                ctx.storage_state(path=str(self.auth_state_path))
                self.cleanup_qr()
                return "LOGIN_SUCCESS", None
            except PwTimeout:
                self.cleanup_qr()
                return "LOGIN_TIMEOUT", None
            except Exception:
                self.cleanup_qr()
                return "LOGIN_FAILED", None
            finally:
                ctx.close()
                browser.close()
