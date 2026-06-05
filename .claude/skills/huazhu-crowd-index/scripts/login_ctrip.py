"""
携程登录脚本
独立负责登录状态检查、按需扫码/手机号登录和 Cookie 持久化。

参照 xiaohongshu-scraper/scripts/login_xhs.py 的范式：
- 复用 ctrip_auth.json（storage_state）
- 输出 COOKIE_FINGERPRINT 便于排查 cookie 一致性
- --check-only 仅检查；否则拉起浏览器等待人工登录
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

from ctrip_selectors import CtripSelectors as S

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

SCRIPT_DIR = Path(__file__).parent.resolve()
AUTH_STATE_PATH = (SCRIPT_DIR / "ctrip_auth.json").resolve()
LOGIN_SHOT_PATH = (SCRIPT_DIR / "ctrip_login.png").resolve()


def build_cookie_fingerprint(path: Path) -> dict:
    resolved = path.resolve()
    fingerprint = {"path": str(resolved), "exists": resolved.exists()}
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


class CtripLogin:
    def __init__(self):
        # 强制有头模式：无 DISPLAY 时报错退出
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            print("[✗] 检测到无 DISPLAY 环境变量", file=sys.stderr, flush=True)
            print("    请先启动虚拟显示器:", file=sys.stderr, flush=True)
            print("    Xvfb :99 -screen 0 1920x1080x24 &", file=sys.stderr, flush=True)
            print("    export DISPLAY=:99", file=sys.stderr, flush=True)
            sys.exit(1)

        self.auth_state_path = AUTH_STATE_PATH
        self.auth_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.shot_path = LOGIN_SHOT_PATH

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
        ctx_kw = {"locale": "zh-CN", "timezone_id": "Asia/Shanghai"}
        if self.auth_state_path.exists():
            try:
                return browser.new_context(storage_state=str(self.auth_state_path), **ctx_kw)
            except Exception as exc:
                print(f"[!] Cookie 加载失败，改用空白上下文: {exc}", flush=True)
        return browser.new_context(**ctx_kw)

    @staticmethod
    def _logged_in_now(page) -> bool:
        """
        判定当前是否已登录：
        - 必须在携程站内且非 passport/login 页（点「登录」会跳到 passport，期间登录按钮也消失，需排除）
        - 首页「登录」按钮(LOGOUT_MARKER) 消失
        """
        url = page.url or ""
        if "passport" in url or "/login" in url:
            return False
        if "ctrip.com" not in url:
            return False
        try:
            return page.locator(S.LOGOUT_MARKER).count() == 0
        except Exception:
            return False

    def _is_logged_in(self, page) -> bool:
        page.goto(S.HOME_URL, wait_until="domcontentloaded")
        try:
            page.wait_for_timeout(2500)
            return self._logged_in_now(page)
        except Exception:
            return False

    def _cleanup_shot(self):
        if os.path.exists(self.shot_path):
            try:
                os.remove(self.shot_path)
            except OSError:
                pass

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
                    print("NEED_LOGIN", flush=True)
                    return 1

                # 截图当前页面（含登录入口）供用户参考，提示人工登录
                try:
                    page.screenshot(path=str(self.shot_path))
                    print(f"NEED_LOGIN:{self.shot_path}", flush=True)
                except Exception:
                    print("NEED_LOGIN", flush=True)

                print(
                    f"[*] 请在弹出的浏览器中点击右上角「登录」并完成扫码/手机号登录，最长等待 {timeout}s ...",
                    flush=True,
                )
                print("[*] 登录成功后页面会自动跳回携程，无需其他操作。", flush=True)

                # 轮询等待登录完成：跳回携程站内且登录按钮消失，连续两次确认避免跳转瞬间误判
                waited = 0
                interval = 3
                confirms = 0
                while waited < timeout:
                    page.wait_for_timeout(interval * 1000)
                    waited += interval
                    if self._logged_in_now(page):
                        confirms += 1
                        if confirms >= 2:
                            break
                    else:
                        confirms = 0
                else:
                    print("LOGIN_TIMEOUT", flush=True)
                    return 2

                page.wait_for_timeout(2000)  # 等 cookie 写入
                self._persist_auth_state(ctx, "login-success")
                self._cleanup_shot()
                print("LOGIN_SUCCESS", flush=True)
                return 0
            except PwTimeout:
                self._cleanup_shot()
                print("LOGIN_TIMEOUT", flush=True)
                return 2
            except Exception as exc:
                self._cleanup_shot()
                print(f"LOGIN_FAILED: {exc}", flush=True)
                return 1
            finally:
                ctx.close()
                browser.close()


def main():
    parser = argparse.ArgumentParser(description="携程登录工具")
    parser.add_argument("--check-only", action="store_true", help="仅检查 Cookie 是否有效")
    parser.add_argument("--timeout", type=int, default=180, help="登录等待超时秒数，默认 180")
    args = parser.parse_args()

    login = CtripLogin()
    code = login.run(check_only=args.check_only, timeout=args.timeout)
    sys.exit(code)


if __name__ == "__main__":
    main()
