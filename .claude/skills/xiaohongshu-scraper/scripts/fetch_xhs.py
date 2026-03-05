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

from playwright.sync_api import sync_playwright, Page, TimeoutError as PwTimeout

# Windows 兼容：强制 UTF-8 输出
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 加载环境变量
load_dotenv()


class XHSScraper:
    def __init__(
        self,
        headless: bool = None,
        max_posts: int = 10,
        search_strategy: list = None,
        seen_ids_path: str = "",
        hyperlinks: bool = False,  # 是否启用超链接功能
    ):
        self.headless = headless
        if self.headless is None:
            if sys.platform != 'win32' and not os.environ.get('DISPLAY'):
                self.headless = True
            else:
                self.headless = False

        self.max_posts = min(max_posts, 100)  # 硬上限 100
        self.search_strategy = search_strategy if search_strategy is not None else []
        self.seen_ids_path = Path(seen_ids_path) if seen_ids_path else None
        self.hyperlinks = hyperlinks  # 超链接功能开关
        self.auth_state_path = os.environ.get(
            'XHS_AUTH_STATE',
            '.claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json'
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
                    print(f"[*] Cookie 已加载: {self.auth_state_path}", flush=True)
                except Exception as e:
                    print(f"[!] Cookie 加载失败: {e}", flush=True)
            if ctx is None:
                ctx = browser.new_context()

            page = ctx.new_page()

            # 1) 搜索 + 抓取（均分 + 回收策略）
            all_posts = []
            seen = self._load_seen_ids()
            new_seen_ids = set()
            remaining_total = self.max_posts
            for idx, kw in enumerate(keywords):
                if remaining_total <= 0:
                    break
                remaining_kws = len(keywords) - idx
                quota = remaining_total // remaining_kws  # 均分
                if remaining_total % remaining_kws != 0:
                    quota += 1  # 余数给当前关键词多 1 篇
                print(f"\n[*] 搜索关键词: {kw}  (配额 {quota}, 总剩余 {remaining_total})", flush=True)
                posts = self._search_keyword(page, kw, quota, seen, new_seen_ids)
                all_posts.extend(posts)
                remaining_total -= len(posts)  # 回收：实际抓到的扣减，未用完的自动流入后续

            self._append_seen_ids(new_seen_ids)

            # 2) 输出
            output_data = {
                "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "keywords": keywords,
                "search_strategy": self.search_strategy,
                "posts": all_posts,
            }
            out = json.dumps(output_data, ensure_ascii=False, indent=2)
            if output_file:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                Path(output_file).write_text(out, encoding="utf-8")
                print(f"\n[✓] 共 {len(all_posts)} 篇 → {output_file}", flush=True)

                # 生成 id_url_map.json（超链接启用时）
                if self.hyperlinks and output_file:
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
            else:
                print("\n" + out)

            ctx.close()
            browser.close()

    def _is_not_logged_in(self, page: Page) -> bool:
        if "login" in page.url.lower():
            return True
        try:
            login_modal = page.locator(S.LOGIN_MODAL)
            if login_modal.count() > 0 and login_modal.first.is_visible():
                return True
            qr_code = page.locator(S.QR_CODE_IMAGE)
            if qr_code.count() > 0 and qr_code.first.is_visible():
                return True
            login_btn = page.locator(f"text={S.LOGIN_BUTTON_TEXT}")
            if login_btn.count() > 0 and login_btn.first.is_visible():
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _exit_not_logged_in():
        print("[✗] 检测到未登录，请先执行 xiaohongshu-login skill", flush=True)
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
            print("  [!] 搜索结果加载超时", flush=True)
            return []

        self._sleep(2, 4)

        # 收集帖子链接 — 滚动加载瀑布流以获取更多结果
        hrefs = []
        max_scroll_rounds = 10  # 最多滚动 10 轮，防止无限循环
        prev_count = 0
        for scroll_round in range(max_scroll_rounds):
            link_els = page.locator(S.POST_LINK).all()
            for el in link_els:
                href = el.get_attribute("href")
                if not href:
                    continue
                full = ("https://www.xiaohongshu.com" + href) if href.startswith("/") else href
                note_id = href.split("/")[-1].split("?")[0]
                if note_id not in seen:
                    seen.add(note_id)
                    new_seen_ids.add(note_id)
                    hrefs.append(full)

            # 已经收集到足够的链接，停止滚动
            if len(hrefs) >= limit:
                break

            # 如果这一轮没有新链接出现，说明已到底部
            if len(hrefs) == prev_count:
                break
            prev_count = len(hrefs)

            # 向下滚动触发瀑布流加载
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self._sleep(2, 4)

        print(f"  找到 {len(hrefs)} 篇（去重后），抓前 {limit} 篇", flush=True)

        results = []
        for i, post_url in enumerate(hrefs[:limit]):
            print(f"  [{i+1}/{min(limit,len(hrefs))}] {post_url[:80]}…", flush=True)
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
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            page.wait_for_selector("#detail-title, .title, .note-content", timeout=10000)
            self._sleep(1, 2)
        except PwTimeout:
            if self._is_not_logged_in(page):
                self._exit_not_logged_in()
            print("    [!] 帖子加载超时，跳过", flush=True)
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

        # 从 URL 中提取帖子 ID
        # URL 格式: https://www.xiaohongshu.com/explore/{note_id} 或 /discovery/item/{note_id}
        post_id = ""
        if url:
            # 去除查询参数和尾部斜杠
            clean_url = url.rstrip("/").split("?")[0]
            post_id = clean_url.split("/")[-1] if clean_url else ""

        return {
            "title":    title,
            "content":  content,
            "author":   author,
            "date":     date,
            "likes":    likes,
            "collects": collects,
            "comments_count": chat,
            "comments": comments,
            "url":      url,      # 保存完整 URL
            "post_id":  post_id,  # 保存帖子 ID
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
    parser.add_argument("--max-posts", type=int, required=True,
                        help="最多抓取帖子数 (上限 100)")
    parser.add_argument("--output", default="",
                        help="JSON 输出文件路径")
    parser.add_argument("--headless", action="store_true",
                        help="强制无头模式")
    parser.add_argument("--search-strategy", default="",
                        help="搜索策略 JSON 字符串，包含 keyword、posts_count、intent")
    parser.add_argument("--seen-ids", default="",
                        help="跨调用去重文件路径（每行一个 note_id）")
    parser.add_argument("--hyperlinks", action="store_true",
                        help="启用超链接功能，生成 id_url_map.json")

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
        headless=True if args.headless else None,
        max_posts=args.max_posts,
        search_strategy=search_strategy,
        seen_ids_path=args.seen_ids,
        hyperlinks=args.hyperlinks,
    )
    scraper.run(keywords=kws, output_file=args.output)
