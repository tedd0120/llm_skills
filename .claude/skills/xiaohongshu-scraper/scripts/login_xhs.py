"""
小红书登录脚本
独立负责登录状态检查、按需二维码登录和 Cookie 持久化。
"""

import argparse
import hashlib
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

SCRAPER_SCRIPT_DIR = Path(__file__).parent.resolve()
AUTH_STATE_PATH = (SCRAPER_SCRIPT_DIR / "xhs_auth.json").resolve()
QR_IMAGE_PATH = (SCRAPER_SCRIPT_DIR / "xhs_qr_login.png").resolve()


def build_cookie_fingerprint(path: Path) -> dict:
    resolved = path.resolve()
    fingerprint = {
        "path": str(resolved),
        "exists": resolved.exists(),
    }
    if not resolved.exists():
        return fingerprint

    stat = resolved.stat()
    fingerprint["mtime"] = stat.st_mtime
    fingerprint["size"] = stat.st_size
    fingerprint["sha256"] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return fingerprint


def format_cookie_fingerprint(fingerprint: dict) -> str:
    if not fingerprint.get("exists"):
        return f"path={fingerprint['path']} exists=False"
    return (
        f"path={fingerprint['path']} exists=True "
        f"mtime={fingerprint['mtime']:.6f} size={fingerprint['size']} "
        f"sha256={fingerprint['sha256']}"
    )


class XHSLogin:
    def __init__(self):
        # 强制有头模式：在无 DISPLAY 时报错退出
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            print("[✗] 检测到无 DISPLAY 环境变量", file=sys.stderr, flush=True)
            print("    请先启动虚拟显示器:", file=sys.stderr, flush=True)
            print("    Xvfb :99 -screen 0 1920x1080x24 &", file=sys.stderr, flush=True)
            print("    export DISPLAY=:99", file=sys.stderr, flush=True)
            sys.exit(1)

        self.auth_state_path = AUTH_STATE_PATH
        self.auth_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.qr_path = QR_IMAGE_PATH

    def _print_cookie_fingerprint(self, stage: str):
        fingerprint = build_cookie_fingerprint(self.auth_state_path)
        print(f"COOKIE_FINGERPRINT[{stage}] {format_cookie_fingerprint(fingerprint)}", flush=True)
        return fingerprint

    def _persist_auth_state(self, ctx, stage: str):
        ctx.storage_state(path=str(self.auth_state_path))
        fingerprint = self._print_cookie_fingerprint(stage)
        if not fingerprint.get("exists"):
            raise RuntimeError("Cookie 文件写入失败")
        return fingerprint

    def _build_context(self, browser):
        self._print_cookie_fingerprint("login-before-load")
        if self.auth_state_path.exists():
            try:
                return browser.new_context(storage_state=str(self.auth_state_path))
            except Exception as exc:
                print(f"[!] Cookie 加载失败，改用空白上下文: {exc}", flush=True)
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

            # 必须验证搜索结果卡片存在，才算登录成功
            post_cards = page.locator(S.POST_CARD)
            return post_cards.count() > 0
        except Exception:
            return False

    def _cleanup_qr(self):
        if os.path.exists(self.qr_path):
            os.remove(self.qr_path)

    @staticmethod
    def _emit_need_login(check_only: bool, qr_path: str):
        if check_only:
            print("NEED_LOGIN", flush=True)
        else:
            print(f"NEED_LOGIN:{qr_path}", flush=True)

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
                    self._persist_auth_state(ctx, "login-ok")
                    print("LOGIN_OK", flush=True)
                    return 0

                if check_only:
                    self._emit_need_login(check_only=True, qr_path=self.qr_path)
                    return 1

                login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
                if self._safe_visible(login_btn):
                    login_btn.first.click()

                page.wait_for_selector(S.QR_CODE_IMAGE, state="visible", timeout=15000)
                modal = page.locator(S.LOGIN_MODAL)
                modal.screenshot(path=self.qr_path)
                self._emit_need_login(check_only=False, qr_path=self.qr_path)

                page.wait_for_selector(S.LOGIN_MODAL, state="hidden", timeout=timeout * 1000)
                # 等待页面完全加载，确保所有 Cookie 写入完毕
                page.wait_for_timeout(3000)
                # 扫码弹窗消失即视为登录成功，不再用搜索页验证（搜索页可能被风控）
                self._persist_auth_state(ctx, "login-success")
                self._cleanup_qr()
                print("LOGIN_SUCCESS", flush=True)
                return 0
            except PwTimeout:
                self._cleanup_qr()
                print("LOGIN_TIMEOUT", flush=True)
                return 2
            except Exception:
                self._cleanup_qr()
                print("LOGIN_FAILED", flush=True)
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
