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
from pathlib import Path
from dotenv import load_dotenv

# 确保能导入同目录下的 selectors
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from selectors import XHSSelectors as S

from playwright.sync_api import sync_playwright, Page, BrowserContext, TimeoutError as PwTimeout

# 加载环境变量
load_dotenv()


class XHSScraper:
    def __init__(self, headless: bool = None, max_posts: int = 10):
        self.headless = headless
        if self.headless is None:
            if sys.platform != 'win32' and not os.environ.get('DISPLAY'):
                self.headless = True
            else:
                self.headless = False

        self.max_posts = min(max_posts, 20)  # 硬上限 20
        self.auth_state_path = os.environ.get(
            'XHS_AUTH_STATE',
            '.agent/skills/xiaohongshu-scraper/scripts/xhs_auth.json'
        )
        Path(self.auth_state_path).parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sleep(lo=3, hi=8):
        time.sleep(random.uniform(lo, hi))

    @staticmethod
    def _txt(page: Page, sel: str, default: str = "") -> str:
        loc = page.locator(sel)
        if loc.count() > 0:
            return loc.first.text_content().strip()
        return default

    # ------------------------------------------------------------------
    # 入口
    # ------------------------------------------------------------------
    def run(self, keywords: list, output_file: str = ""):
        with sync_playwright() as pw:
            launch_kw = {"headless": self.headless}
            if sys.platform == 'win32' and not self.headless:
                launch_kw["channel"] = "msedge"

            browser = pw.chromium.launch(**launch_kw)

            # Cookie
            ctx = None
            if os.path.exists(self.auth_state_path):
                try:
                    ctx = browser.new_context(storage_state=self.auth_state_path)
                    print(f"[*] Cookie 已加载: {self.auth_state_path}")
                except Exception as e:
                    print(f"[!] Cookie 加载失败: {e}")
            if ctx is None:
                ctx = browser.new_context()

            page = ctx.new_page()

            # 1) 登录
            self._ensure_login(page, ctx)

            # 2) 搜索 + 抓取
            all_posts = []
            seen = set()
            for kw in keywords:
                if len(all_posts) >= self.max_posts:
                    break
                remain = self.max_posts - len(all_posts)
                print(f"\n[*] 搜索关键词: {kw}  (剩余额度 {remain})")
                posts = self._search_keyword(page, kw, remain, seen)
                all_posts.extend(posts)

            # 3) 输出
            out = json.dumps(all_posts, ensure_ascii=False, indent=2)
            if output_file:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                Path(output_file).write_text(out, encoding="utf-8")
                print(f"\n[✓] 共 {len(all_posts)} 篇 → {output_file}")
            else:
                print("\n" + out)

            ctx.close()
            browser.close()

    # ------------------------------------------------------------------
    # 登录
    # ------------------------------------------------------------------
    def _ensure_login(self, page: Page, ctx: BrowserContext):
        print("[*] 检查登录状态…")
        page.goto("https://www.xiaohongshu.com/explore", wait_until="domcontentloaded")
        self._sleep(2, 4)

        # 如果搜索框存在且没有登录弹窗 → 已登录
        try:
            page.wait_for_selector(S.SEARCH_INPUT, timeout=8000)
            # 进一步确认：有没有"登录"按钮可见
            login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
            if login_btn.count() > 0 and login_btn.first.is_visible():
                self._qr_login(page, ctx)
            else:
                print("[*] 已登录 ✓")
        except PwTimeout:
            self._qr_login(page, ctx)

    def _qr_login(self, page: Page, ctx: BrowserContext):
        print("[!] 需要扫码登录")
        login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
        if login_btn.count() > 0 and login_btn.first.is_visible():
            login_btn.first.click()
            self._sleep(1, 2)

        try:
            qr = page.locator(S.QR_CODE_IMAGE)
            qr.wait_for(state="visible", timeout=15000)
            qr_path = os.path.abspath("xhs_qr_login.png")
            qr.screenshot(path=qr_path)
            print(f"[!] 请扫码: {qr_path}")

            # 等待登录完成（登录框消失）
            page.wait_for_selector(S.LOGIN_MODAL, state="hidden", timeout=120000)
            print("[*] 登录成功 ✓")

            ctx.storage_state(path=self.auth_state_path)
            print(f"[*] Cookie 已保存 → {self.auth_state_path}")
            if os.path.exists(qr_path):
                os.remove(qr_path)
            self._sleep(2, 3)
        except PwTimeout:
            print("[✗] 扫码超时，退出。")
            sys.exit(1)

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------
    def _search_keyword(self, page: Page, keyword: str, limit: int, seen: set) -> list:
        url = (
            f"https://www.xiaohongshu.com/search_result"
            f"?keyword={keyword}&source=web_search_result_notes"
        )
        page.goto(url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector(S.POST_CARD, timeout=10000)
        except PwTimeout:
            print("  [!] 搜索结果加载超时")
            return []

        self._sleep(2, 4)

        # 收集帖子链接（使用带 xsec_token 的 /search_result/ 链接）
        link_els = page.locator(S.POST_LINK).all()
        hrefs = []
        for el in link_els:
            href = el.get_attribute("href")
            if not href:
                continue
            full = ("https://www.xiaohongshu.com" + href) if href.startswith("/") else href
            # 去重 key = note id
            note_id = href.split("/")[-1].split("?")[0]
            if note_id not in seen:
                seen.add(note_id)
                hrefs.append(full)

        print(f"  找到 {len(hrefs)} 篇（去重后），抓前 {limit} 篇")

        results = []
        for i, post_url in enumerate(hrefs[:limit]):
            print(f"  [{i+1}/{min(limit,len(hrefs))}] {post_url[:80]}…")
            data = self._extract_post(page, post_url)
            if data:
                results.append(data)
            self._sleep(3, 8)
        return results

    # ------------------------------------------------------------------
    # 帖子提取
    # ------------------------------------------------------------------
    def _extract_post(self, page: Page, url: str) -> dict | None:
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_selector("#detail-title, .title, .note-content", timeout=10000)
            self._sleep(1, 2)
        except PwTimeout:
            print("    [!] 帖子加载超时，跳过")
            return None

        title   = self._txt(page, "#detail-title") or self._txt(page, ".title")
        content = self._txt(page, ".note-content") or self._txt(page, "#detail-desc")
        author  = self._txt(page, ".username")
        date    = self._txt(page, ".bottom-container .date") or self._txt(page, ".date")
        likes   = self._txt(page, ".like-wrapper .count",    "0")
        collects= self._txt(page, ".collect-wrapper .count", "0")
        chat    = self._txt(page, ".chat-wrapper .count",    "0")

        # 评论
        comments = self._extract_comments(page)

        return {
            "url":      url,
            "title":    title,
            "content":  content,
            "author":   author,
            "date":     date,
            "likes":    likes,
            "collects": collects,
            "comments_count": chat,
            "comments": comments,
        }

    def _extract_comments(self, page: Page) -> list[str]:
        comments = []
        try:
            # 展开更多评论（最多 2 次）
            for _ in range(2):
                more = page.locator("text=展开更多评论")
                if more.count() > 0 and more.first.is_visible():
                    more.first.click()
                    self._sleep(1, 2)
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
    parser.add_argument("--max-posts", type=int, default=10,
                        help="最多抓取帖子数 (默认 10, 上限 20)")
    parser.add_argument("--output", default="",
                        help="JSON 输出文件路径")
    parser.add_argument("--headless", action="store_true",
                        help="强制无头模式")

    args = parser.parse_args()
    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]

    scraper = XHSScraper(
        headless=True if args.headless else None,
        max_posts=args.max_posts,
    )
    scraper.run(keywords=kws, output_file=args.output)
