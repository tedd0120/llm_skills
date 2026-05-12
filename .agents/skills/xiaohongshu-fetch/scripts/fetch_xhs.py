"""
小红书内容抓取主脚本
基于 Playwright 实现，支持扫码登录、搜索、抓取正文和评论区。

选择器基于 2026-02-26 实际 DOM 分析验证。
"""

import sys
import os
import json
import time
import random
import argparse
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# 导入同目录下的选择器
from xhs_selectors import XHSSelectors as S

from playwright.sync_api import sync_playwright, Page, TimeoutError as PwTimeout
from playwright_stealth import Stealth

# Windows 兼容：强制 UTF-8 输出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 加载环境变量
load_dotenv()

FETCH_SCRIPT_DIR = Path(__file__).parent.resolve()
AUTH_STATE_PATH = (
    FETCH_SCRIPT_DIR.parent.parent / "xiaohongshu-scraper" / "scripts" / "xhs_auth.json"
).resolve()


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


class XHSScraper:
    def __init__(
        self,
        max_posts: int = 10,
        search_strategy: list = None,
        seen_ids_path: str = "",
        hyperlinks: bool = False,
        safe_mode: bool = False,
        speed_mode: bool = False,
    ):
        # 强制有头模式：在无 DISPLAY 时报错退出
        if sys.platform != 'win32' and not os.environ.get('DISPLAY'):
            print("[✗] 检测到无 DISPLAY 环境变量", file=sys.stderr, flush=True)
            print("    请先启动虚拟显示器:", file=sys.stderr, flush=True)
            print("    Xvfb :99 -screen 0 1920x1080x24 &", file=sys.stderr, flush=True)
            print("    export DISPLAY=:99", file=sys.stderr, flush=True)
            sys.exit(1)

        self.max_posts = min(max_posts, 100)  # 硬上限 100
        self.search_strategy = search_strategy if search_strategy is not None else []
        self.seen_ids_path = Path(seen_ids_path) if seen_ids_path else None
        self.hyperlinks = hyperlinks
        self.safe_mode = safe_mode
        self.speed_mode = speed_mode
        self.auth_state_path = AUTH_STATE_PATH

        # 启动模式横幅
        if self.speed_mode:
            print("[⚡] 极速模式 — 已去除所有延时", flush=True)
        elif self.safe_mode:
            print("[🛡️] 安全模式 — 延迟增大，模拟人类阅读节奏", flush=True)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sleep(lo=3, hi=8):
        """静态方法：保持原有行为（用于外部调用兼容）"""
        time.sleep(random.uniform(lo, hi))

    def _do_sleep(self, lo=3, hi=8):
        """实例方法：极速模式跳过，安全模式增大延迟+阅读停顿"""
        if self.speed_mode:
            return
        if self.safe_mode:
            lo_safe = lo * 2.5
            hi_safe = hi * 2.5 + random.uniform(0, 2)
            time.sleep(random.uniform(lo_safe, hi_safe))
            if random.random() < 0.10:
                reading_pause = random.uniform(5, 15)
                print(f"    [safe-mode] reading pause {reading_pause:.1f}s", flush=True)
                time.sleep(reading_pause)
        else:
            time.sleep(random.uniform(lo, hi))

    def _print_cookie_fingerprint(self, stage: str):
        fingerprint = build_cookie_fingerprint(self.auth_state_path)
        print(f"COOKIE_FINGERPRINT[{stage}] {format_cookie_fingerprint(fingerprint)}", flush=True)
        return fingerprint

    @staticmethod
    def _txt(page: Page, sel: str, default: str = "") -> str:
        loc = page.locator(sel)
        if loc.count() > 0:
            return loc.first.text_content().strip()
        return default

    def _load_seen_ids(self) -> set:
        if not self.seen_ids_path:
            return set()

        self.seen_ids_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.seen_ids_path.exists():
            self.seen_ids_path.touch()
            return set()

        content = self.seen_ids_path.read_text(encoding="utf-8")
        return {line.strip() for line in content.splitlines() if line.strip()}

    def _append_seen_ids(self, new_ids: set):
        if not self.seen_ids_path or not new_ids:
            return

        payload = "".join(f"{note_id}\n" for note_id in sorted(new_ids))
        with self.seen_ids_path.open("a", encoding="utf-8") as f:
            f.write(payload)

    @staticmethod
    def _parse_int(value: str, default: int = 0) -> int:
        """将字符串转换为整数，失败返回默认值"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _save_results(self, all_posts: list, output_file: str, keywords: list):
        """保存抓取结果到文件"""
        if not all_posts or not output_file:
            return

        output_data = {
            "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "keywords": keywords,
            "search_strategy": self.search_strategy,
            "posts": all_posts,
        }
        out = json.dumps(output_data, ensure_ascii=False, indent=2)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_text(out, encoding="utf-8")
        print(f"\n[✓] 共 {len(all_posts)} 篇 → {output_file}", flush=True)

        # 生成 id_url_map.json（超链接启用时）
        if self.hyperlinks:
            id_url_map = {}
            for post in all_posts:
                post_id = post.get("post_id", "")
                url = post.get("url", "")
                if post_id and url:
                    id_url_map[post_id] = url

            if id_url_map:
                output_dir = Path(output_file).parent
                map_file = output_dir / "id_url_map.json"
                map_file.write_text(
                    json.dumps(id_url_map, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                print(f"[✓] ID-URL 映射 → {map_file}", flush=True)

    @staticmethod
    def _save_debug_screenshot(page: Page, label: str):
        try:
            path = Path(f"xhs_debug_{label}_{int(time.time())}.png")
            page.screenshot(path=str(path))
            print(f"[DEBUG] 截图已保存: {path}", flush=True)
        except Exception:
            pass

    def _handle_captcha_verification(self, page: Page) -> str | None:
        """
        处理风控验证码页面：
        1. 等待二维码加载完成
        2. 截图保存
        3. 返回截图路径供用户扫码
        """
        captcha_screenshot = FETCH_SCRIPT_DIR / "xhs_captcha_qr.png"

        try:
            # 等待二维码图片加载完成（最长等待 10 秒）
            page.wait_for_selector(S.QR_CODE_IMAGE, state="visible", timeout=10000)

            # 额外等待确保图片完全渲染
            page.wait_for_timeout(500)

            # 截取二维码区域
            qr_element = page.locator(S.QR_CODE_IMAGE)
            if qr_element.count() > 0:
                qr_element.first.screenshot(path=str(captcha_screenshot))
            else:
                page.screenshot(path=str(captcha_screenshot))

            print(f"[✓] 验证码二维码已保存: {captcha_screenshot}", flush=True)
            return str(captcha_screenshot)
        except Exception as e:
            # 降级：截图整个页面
            print(f"[!] 二维码截图失败，降级截图整个页面: {e}", flush=True)
            page.screenshot(path=str(captcha_screenshot))
            return str(captcha_screenshot)

    # ------------------------------------------------------------------
    # 入口
    # ------------------------------------------------------------------
    def run(self, keywords: list, output_file: str = ""):
        with sync_playwright() as pw:
            launch_kw = {"headless": False}
            if sys.platform == 'win32':
                launch_kw["channel"] = "msedge"
                launch_kw["args"] = ["--window-position=-2400,-2400"]

            browser = pw.chromium.launch(**launch_kw)

            ctx_kw = {
                "viewport": {"width": 1280, "height": 800},
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
            }

            # Cookie
            ctx = None
            fingerprint = self._print_cookie_fingerprint("fetch-before-load")
            if self.auth_state_path.exists():
                try:
                    ctx = browser.new_context(storage_state=str(self.auth_state_path), **ctx_kw)
                    print(f"[*] Cookie 已加载: {self.auth_state_path}", flush=True)
                except Exception as e:
                    print(f"[!] Cookie 加载失败: {e}", flush=True)
            else:
                print(f"[!] Cookie 文件不存在: {fingerprint['path']}", flush=True)
            if ctx is None:
                ctx = browser.new_context(**ctx_kw)

            page = ctx.new_page()
            Stealth().apply_stealth_sync(page)

            # 1) 搜索 + 抓取（strategy 优先，回收策略兜底）
            all_posts = []
            seen = self._load_seen_ids()
            new_seen_ids = set()
            remaining_total = self.max_posts

            # 构建 keyword→limit 映射（从 search_strategy）
            strategy_limits = {}
            if self.search_strategy:
                for item in self.search_strategy:
                    kw = item.get("keyword", "")
                    limit = item.get("limit") or item.get("posts_count") or item.get("count")
                    if kw and limit:
                        strategy_limits[kw] = int(limit)

            try:
                for idx, kw in enumerate(keywords):
                    if remaining_total <= 0:
                        break
                    # 优先使用 strategy 配置的 limit，否则均分
                    if kw in strategy_limits:
                        quota = min(strategy_limits[kw], remaining_total)
                    else:
                        remaining_kws = len(keywords) - idx
                        quota = remaining_total // remaining_kws
                        if remaining_total % remaining_kws != 0:
                            quota += 1
                    print(f"\n[*] 搜索关键词: {kw}  (配额 {quota}, 总剩余 {remaining_total})", flush=True)
                    try:
                        posts = self._search_keyword(page, kw, quota, seen, new_seen_ids)
                        all_posts.extend(posts)
                        remaining_total -= len(posts)  # 回收：实际抓到的扣减，未用完的自动流入后续
                    except Exception as e:
                        print(f"[!] 关键词 '{kw}' 抓取失败: {e}", flush=True)
                        self._save_debug_screenshot(page, f"keyword_error_{kw[:10]}")
                        continue  # 继续下一个关键词
            finally:
                # 无论是否异常，都保存已抓取的数据
                if all_posts:
                    self._save_results(all_posts, output_file, keywords)
                    self._append_seen_ids(new_seen_ids)
                elif output_file:
                    print(f"\n[!] 未抓取到任何帖子", flush=True)

            ctx.close()
            browser.close()

    def _is_not_logged_in(self, page: Page) -> bool:
        """
        检测是否处于未登录状态（需要强制登录才能继续）。

        注意：小红书页面经常会有"扫码关注作者"、"扫码下载APP"等二维码，
        以及"登录后关注"等按钮，这些并不意味着用户未登录。
        只有出现遮罩层 + 登录弹窗的组合，才是真正的强制登录状态。
        """
        # 1. URL 检测
        url_lower = page.url.lower()
        if "website-login/error" in url_lower:
            # 风控限速，不是真正的未登录
            error_msg = ""
            if "error_msg=" in page.url:
                import urllib.parse
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(page.url).query)
                error_msg = urllib.parse.unquote(qs.get("error_msg", [""])[0])
            print(f"[!] 检测到风控限速跳转: {error_msg or page.url}", flush=True)
            self._save_debug_screenshot(page, "rate_limit")
            if not self.speed_mode:
                print("[!] 等待 30 秒，请查看浏览器页面...", flush=True)
                time.sleep(30)
            return True

        # 2. 风控验证码页面检测（二次扫码验证）
        if "website-login/captcha" in url_lower:
            print(f"[!] 检测到风控验证码页面: {page.url}", flush=True)

            # 等待并截取二维码
            qr_path = self._handle_captcha_verification(page)

            if qr_path:
                # 输出标准事件，供编排层识别
                print(f"NEED_CAPTCHA:{qr_path}", flush=True)

            # 轮询等待用户扫码完成
            print("[!] 请查看截图扫码验证，验证完成后将自动继续...", flush=True)
            for i in range(60):  # 最长等待 180 秒
                time.sleep(3)
                current_url = page.url.lower()

                # 检测1: URL 跳转到正常页面（搜索结果、帖子等）
                if any(x in current_url for x in ["search_result", "/explore/", "/discovery/"]):
                    print("[✓] 验证完成（URL跳转），继续抓取...", flush=True)
                    return False

                # 检测2: 离开 captcha 页面
                if "captcha" not in current_url:
                    print("[✓] 验证完成（离开captcha），继续抓取...", flush=True)
                    return False

                # 检测3: 二维码元素消失（扫码成功）
                try:
                    qr_element = page.locator(S.QR_CODE_IMAGE)
                    if qr_element.count() == 0 or not qr_element.first.is_visible():
                        print("[✓] 验证完成（二维码消失），继续抓取...", flush=True)
                        # 等待页面跳转
                        page.wait_for_timeout(1000)
                        return False
                except Exception:
                    print("[✓] 验证完成（元素异常），继续抓取...", flush=True)
                    return False

            print("[✗] 验证超时", flush=True)
            return True

        if "login" in url_lower:
            print(f"[!] 检测到登录页跳转: {page.url}", flush=True)
            self._save_debug_screenshot(page, "login_redirect")
            # 等待用户扫码验证
            print("[!] 请在浏览器窗口中扫码验证，扫码完成后将自动继续...", flush=True)
            # 等待最多 120 秒，每 3 秒检查一次是否已离开登录页
            for _ in range(40):
                time.sleep(3)
                if "login" not in page.url.lower():
                    print("[✓] 验证完成，继续抓取...", flush=True)
                    return False
            print("[✗] 验证超时", flush=True)
            return True

        try:
            # 2. 检测验证码/风控页面
            captcha_indicators = [
                "text=请完成验证",
                "text=滑动验证",
                ".captcha-verify",
                "#captcha",
            ]
            for sel in captcha_indicators:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    print(f"[!] 检测到风控验证页: {sel}", flush=True)
                    self._save_debug_screenshot(page, "captcha")
                    if not self.speed_mode:
                        print("[!] 等待 30 秒，请查看浏览器页面...", flush=True)
                        time.sleep(30)
                    return True

            # 3. 检测强制登录弹窗：遮罩层 + 登录弹窗同时出现
            # 这才是真正的"未登录需要登录"状态
            login_modal = page.locator(S.LOGIN_MODAL)
            overlay = page.locator(S.LOGIN_OVERLAY)

            modal_visible = login_modal.count() > 0 and login_modal.first.is_visible()
            overlay_visible = overlay.count() > 0 and overlay.first.is_visible()

            if modal_visible and overlay_visible:
                self._save_debug_screenshot(page, "login_modal")
                if not self.speed_mode:
                    print("[!] 等待 30 秒，请查看浏览器页面...", flush=True)
                    time.sleep(30)
                return True

            # 4. 备用检测：登录弹窗内有明显的"登录"标题且可见
            # 避免误判普通的登录引导按钮
            login_title = page.locator(S.LOGIN_MODAL_TITLE)
            if modal_visible and login_title.count() > 0:
                if login_title.first.is_visible():
                    self._save_debug_screenshot(page, "login_title")
                    if not self.speed_mode:
                        print("[!] 等待 30 秒，请查看浏览器页面...", flush=True)
                        time.sleep(30)
                    return True

        except Exception:
            pass

        return False

    @staticmethod
    def _exit_not_logged_in():
        print("[✗] 检测到登录态异常或风控拦截，请检查 Cookie 或稍后重试", flush=True)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------
    def _search_keyword(self, page: Page, keyword: str, limit: int, seen: set, new_seen_ids: set) -> list:
        url = (
            f"https://www.xiaohongshu.com/search_result"
            f"?keyword={keyword}&source=web_search_result_notes"
        )
        page.goto(url, wait_until="domcontentloaded")
        if self._is_not_logged_in(page):
            self._exit_not_logged_in()

        try:
            page.wait_for_selector(S.POST_CARD, timeout=10000)
        except PwTimeout:
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            print(f"  [!] 搜索结果加载超时 | URL: {page.url} | title: {page.title()}", flush=True)
            self._save_debug_screenshot(page, f"search_timeout_{keyword[:10]}")
            return []

        self._do_sleep(2, 4)

        # 边滚动边点击策略：解决虚拟滚动导致元素不在 DOM 中的问题
        # 关键：每次只处理一个帖子，然后重新获取当前可见元素
        results = []
        processed_ids = set()  # 本次搜索已处理的 note_id（用于去重）
        consecutive_empty_scrolls = 0  # 连续无新内容的滚动次数
        max_empty_scrolls = 3  # 连续 3 次无新内容则停止

        print(f"  开始边滚动边抓取，目标 {limit} 篇", flush=True)

        while len(results) < limit:
            # 每次只获取一个未处理的帖子（确保元素在 DOM 中）
            link_els = page.locator(S.POST_LINK).all()
            target_el = None
            target_note_id = None
            target_url = None

            for el in link_els:
                href = el.get_attribute("href")
                if not href:
                    continue
                note_id = href.split("/")[-1].split("?")[0]
                # 找到第一个未处理的帖子
                if note_id not in processed_ids and note_id not in seen:
                    full_url = ("https://www.xiaohongshu.com" + href) if href.startswith("/") else href
                    target_el = el
                    target_note_id = note_id
                    target_url = full_url
                    break

            # 如果没有找到未处理的帖子，滚动加载更多
            if target_el is None:
                consecutive_empty_scrolls += 1
                if consecutive_empty_scrolls >= max_empty_scrolls:
                    print(f"  连续 {max_empty_scrolls} 次无新内容，停止抓取", flush=True)
                    break
                # 滚动尝试加载更多
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                if self.speed_mode:
                    time.sleep(1)
                elif self.safe_mode:
                    time.sleep(random.uniform(4, 7))
                else:
                    time.sleep(2)
                continue
            else:
                consecutive_empty_scrolls = 0  # 有新内容，重置计数器

            # 处理这一个帖子
            print(f"  [{len(results)+1}/{limit}] {target_url[:60]}…", flush=True)

            try:
                # 滚动到元素可见并点击
                target_el.scroll_into_view_if_needed()
                self._do_sleep(0.3, 0.8)
                target_el.click()

                # 提取帖子数据
                data = self._extract_post_after_click(page, target_url)

                # 关闭详情页返回搜索结果
                close_btn = page.locator(S.CLOSE_BUTTON)
                if close_btn.count() > 0:
                    close_btn.first.click()
                else:
                    page.keyboard.press("Escape")
                self._do_sleep(0.5, 1.5)

                if data:
                    results.append(data)
                    processed_ids.add(target_note_id)
                    new_seen_ids.add(target_note_id)
                    seen.add(target_note_id)
                else:
                    # 提取失败也标记为已处理，避免重复尝试
                    processed_ids.add(target_note_id)

            except Exception as e:
                print(f"    [!] 点击操作失败: {e}", flush=True)
                self._save_debug_screenshot(page, f"click_fail_{len(results)}")
                processed_ids.add(target_note_id)  # 标记为已处理
                # 尝试关闭弹窗
                try:
                    close_btn = page.locator(S.CLOSE_BUTTON)
                    if close_btn.count() > 0:
                        close_btn.first.click()
                except:
                    pass

            self._do_sleep(2, 5)

        print(f"  抓取完成: {len(results)} 篇", flush=True)
        return results

    # ------------------------------------------------------------------
    # 帖子提取（点击导航版）
    # ------------------------------------------------------------------
    def _extract_post_after_click(self, page: Page, expected_url: str) -> dict | None:
        try:
            page.wait_for_selector("#detail-title, .title, .note-content", timeout=10000)
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            self._do_sleep(1, 2)
        except PwTimeout:
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            print("    [!] 帖子加载超时，跳过", flush=True)
            self._save_debug_screenshot(page, "post_timeout_click")
            return None
        return self._extract_post_data(page, expected_url)

    # ------------------------------------------------------------------
    # 帖子提取
    # ------------------------------------------------------------------
    def _extract_post(self, page: Page, url: str) -> dict | None:
        try:
            page.goto(url, wait_until="domcontentloaded")
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            page.wait_for_selector("#detail-title, .title, .note-content", timeout=10000)
            self._do_sleep(1, 2)
        except PwTimeout:
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            print("    [!] 帖子加载超时，跳过", flush=True)
            self._save_debug_screenshot(page, "post_timeout")
            return None
        return self._extract_post_data(page, url)

    def _extract_post_data(self, page: Page, url: str) -> dict | None:
        title   = self._txt(page, "#detail-title") or self._txt(page, ".title")
        content = self._txt(page, ".note-content") or self._txt(page, "#detail-desc")
        author  = self._txt(page, ".username")
        date    = self._txt(page, ".bottom-container .date") or self._txt(page, ".date")
        likes   = self._txt(page, ".like-wrapper .count",    "0")
        collects= self._txt(page, ".collect-wrapper .count", "0")
        chat    = self._txt(page, ".chat-wrapper .count",    "0")

        # 评论
        comments = self._extract_comments(page)

        # 从 URL 中提取帖子 ID
        # URL 格式: https://www.xiaohongshu.com/explore/{note_id} 或 /discovery/item/{note_id}
        post_id = ""
        if url:
            # 去除查询参数和尾部斜杠
            clean_url = url.rstrip("/").split("?")[0]
            post_id = clean_url.split("/")[-1] if clean_url else ""

        result = {
            "title":        title,
            "content":      content,
            "author":       author,
            "date":         date,
            "likes":        self._parse_int(likes),
            "collects":     self._parse_int(collects),
            "comments_count": self._parse_int(chat),
            "comments":     comments,
        }

        # 超链接启用时包含 post_id 和 url
        if self.hyperlinks:
            result["post_id"] = post_id
            result["url"] = url

        return result

    def _extract_comments(self, page: Page) -> list[str]:
        comments = []
        try:
            # 等待评论区加载（功能性等待，极速模式下也需要）
            try:
                page.wait_for_selector(".comment-item", timeout=2000)
            except PwTimeout:
                # 可能真的没有评论，直接返回空
                return comments

            # 展开更多评论（最多 2 次）
            for _ in range(2):
                more = page.locator("text=展开更多评论")
                if more.count() > 0 and more.first.is_visible():
                    more.first.click()
                    # 等待新评论加载（功能性等待，极速模式下也需要）
                    try:
                        page.wait_for_timeout(800)
                    except Exception:
                        pass
                else:
                    break

            items = page.locator(".comment-item .content").all()
            for item in items:
                txt = item.text_content().strip()
                if txt:
                    comments.append(txt)
        except Exception:
            pass
        return comments


# ======================================================================
# CLI
# ======================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="小红书帖子抓取工具 — Playwright + msedge"
    )
    parser.add_argument("--keywords", required=True,
                        help="搜索关键词，多个用逗号分隔")
    parser.add_argument("--max-posts", type=int, required=True,
                        help="最多抓取帖子数 (上限 100)")
    parser.add_argument("--output", default="",
                        help="JSON 输出文件路径")
    parser.add_argument("--search-strategy", default="",
                        help="搜索策略 JSON 字符串，包含 keyword、posts_count、intent")
    parser.add_argument("--seen-ids", default="",
                        help="跨调用去重文件路径（每行一个 note_id）")
    parser.add_argument("--hyperlinks", action="store_true",
                        help="启用超链接功能，生成 id_url_map.json")
    parser.add_argument("--safe-mode", action="store_true",
                        help="安全模式：延迟增大 2.5-3x + 随机阅读停顿，降低风控风险")
    parser.add_argument("--speed-mode", action="store_true",
                        help="极速模式：去除所有随机延时，加速抓取（可能触发风控）")

    args = parser.parse_args()
    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]

    # 解析 search_strategy 参数
    search_strategy = []
    if args.search_strategy:
        try:
            search_strategy = json.loads(args.search_strategy)
            if not isinstance(search_strategy, list):
                print("[!] search_strategy 必须是数组格式", flush=True)
                sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[!] search_strategy JSON 格式错误: {e}", flush=True)
            sys.exit(1)

    scraper = XHSScraper(
        max_posts=args.max_posts,
        search_strategy=search_strategy,
        seen_ids_path=args.seen_ids,
        hyperlinks=args.hyperlinks,
        safe_mode=args.safe_mode,
        speed_mode=args.speed_mode,
    )
    scraper.run(keywords=kws, output_file=args.output)
