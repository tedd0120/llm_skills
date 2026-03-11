"""小红书内容抓取主脚本（codex）。"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PwTimeout, sync_playwright

CORE_DIR = Path(__file__).resolve().parents[2] / "xiaohongshu-core-codex" / "scripts"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from auth import get_auth_state_path
from browser import build_launch_kwargs
from xhs_selectors import XHSSelectors as S


class XHSScraper:
    def __init__(self, max_posts: int = 10, search_strategy: list | None = None, seen_ids_path: str = "", hyperlinks: bool = False):
        self.max_posts = min(max_posts, 100)
        self.search_strategy = search_strategy if search_strategy is not None else []
        self.seen_ids_path = Path(seen_ids_path) if seen_ids_path else None
        self.hyperlinks = hyperlinks
        self.auth_state_path = get_auth_state_path()

    @staticmethod
    def _sleep(lo: int = 3, hi: int = 8) -> None:
        time.sleep(random.uniform(lo, hi))

    @staticmethod
    def _txt(page: Page, sel: str, default: str = "") -> str:
        loc = page.locator(sel)
        if loc.count() > 0:
            text = loc.first.text_content() or ""
            return text.strip()
        return default

    def _load_seen_ids(self) -> set[str]:
        if not self.seen_ids_path:
            return set()
        self.seen_ids_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.seen_ids_path.exists():
            self.seen_ids_path.touch()
            return set()
        content = self.seen_ids_path.read_text(encoding="utf-8")
        return {line.strip() for line in content.splitlines() if line.strip()}

    def _append_seen_ids(self, new_ids: set[str]) -> None:
        if not self.seen_ids_path or not new_ids:
            return
        payload = "".join(f"{note_id}\n" for note_id in sorted(new_ids))
        with self.seen_ids_path.open("a", encoding="utf-8") as f:
            f.write(payload)

    def run(self, keywords: list[str], output_file: str = "") -> None:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**build_launch_kwargs())
            ctx = None
            if self.auth_state_path.exists():
                try:
                    ctx = browser.new_context(storage_state=str(self.auth_state_path))
                    print(f"[*] Cookie 已加载: {self.auth_state_path}", flush=True)
                except Exception as exc:
                    print(f"[!] Cookie 加载失败: {exc}", flush=True)
            if ctx is None:
                ctx = browser.new_context()

            page = ctx.new_page()
            all_posts: list[dict] = []
            seen = self._load_seen_ids()
            new_seen_ids: set[str] = set()
            remaining_total = self.max_posts

            for idx, kw in enumerate(keywords):
                if remaining_total <= 0:
                    break
                remaining_kws = len(keywords) - idx
                quota = remaining_total // remaining_kws
                if remaining_total % remaining_kws != 0:
                    quota += 1
                print(f"\n[*] 搜索关键词: {kw}  (配额 {quota}, 总剩余 {remaining_total})", flush=True)
                posts = self._search_keyword(page, kw, quota, seen, new_seen_ids)
                all_posts.extend(posts)
                remaining_total -= len(posts)

            self._append_seen_ids(new_seen_ids)

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
                if self.hyperlinks:
                    id_url_map = {}
                    for post in all_posts:
                        post_id = post.get("post_id", "")
                        url = post.get("url", "")
                        if post_id and url:
                            id_url_map[post_id] = url
                    if id_url_map:
                        map_file = Path(output_file).parent / "id_url_map.json"
                        map_file.write_text(json.dumps(id_url_map, ensure_ascii=False, indent=2), encoding="utf-8")
                        print(f"[✓] ID-URL 映射 → {map_file}", flush=True)
            else:
                print(f"\n{out}")

            ctx.close()
            browser.close()

    def _is_not_logged_in(self, page: Page) -> bool:
        if "login" in page.url.lower():
            return True
        try:
            login_modal = page.locator(S.LOGIN_MODAL)
            overlay = page.locator(S.LOGIN_OVERLAY)
            modal_visible = login_modal.count() > 0 and login_modal.first.is_visible()
            overlay_visible = overlay.count() > 0 and overlay.first.is_visible()
            if modal_visible and overlay_visible:
                return True
            login_title = page.locator(S.LOGIN_MODAL_TITLE)
            if modal_visible and login_title.count() > 0 and login_title.first.is_visible():
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _exit_not_logged_in() -> None:
        print("[✗] 检测到未登录，请通过 xiaohongshu-scraper-codex 重新执行完整流程", flush=True)
        sys.exit(1)

    def _search_keyword(self, page: Page, keyword: str, limit: int, seen: set[str], new_seen_ids: set[str]) -> list[dict]:
        url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
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
        hrefs: list[str] = []
        max_scroll_rounds = 10
        prev_count = 0
        for _ in range(max_scroll_rounds):
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
            if len(hrefs) >= limit or len(hrefs) == prev_count:
                break
            prev_count = len(hrefs)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self._sleep(2, 4)

        print(f"  找到 {len(hrefs)} 篇（去重后），抓前 {limit} 篇", flush=True)
        results: list[dict] = []
        for i, post_url in enumerate(hrefs[:limit]):
            print(f"  [{i + 1}/{min(limit, len(hrefs))}] {post_url[:80]}…", flush=True)
            data = self._extract_post(page, post_url)
            if data:
                results.append(data)
            self._sleep(3, 8)
        return results

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

        title = self._txt(page, "#detail-title") or self._txt(page, ".title")
        content = self._txt(page, ".note-content") or self._txt(page, "#detail-desc")
        author = self._txt(page, ".username")
        date = self._txt(page, ".bottom-container .date") or self._txt(page, ".date")
        likes = self._txt(page, ".like-wrapper .count", "0")
        collects = self._txt(page, ".collect-wrapper .count", "0")
        chat = self._txt(page, ".chat-wrapper .count", "0")
        comments = self._extract_comments(page)

        clean_url = url.rstrip("/").split("?")[0]
        post_id = clean_url.split("/")[-1] if clean_url else ""
        result = {
            "title": title,
            "content": content,
            "author": author,
            "date": date,
            "likes": likes,
            "collects": collects,
            "comments_count": chat,
            "comments": comments,
        }
        if self.hyperlinks:
            result["post_id"] = post_id
            result["url"] = url
        return result

    def _extract_comments(self, page: Page) -> list[str]:
        comments: list[str] = []
        try:
            for _ in range(2):
                more = page.locator(S.MORE_COMMENTS_BUTTON)
                if more.count() > 0 and more.first.is_visible():
                    more.first.click()
                    self._sleep(1, 2)
                else:
                    break
            items = page.locator(S.COMMENT_CONTENT).all()
            for item in items:
                text = (item.text_content() or "").strip()
                if text:
                    comments.append(text)
        except Exception:
            pass
        return comments


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书帖子抓取工具（codex）")
    parser.add_argument("--keywords", required=True, help="搜索关键词，多个用逗号分隔")
    parser.add_argument("--max-posts", type=int, required=True, help="最多抓取帖子数 (上限 100)")
    parser.add_argument("--output", default="", help="JSON 输出文件路径")
    parser.add_argument("--search-strategy", default="", help="搜索策略 JSON 字符串")
    parser.add_argument("--seen-ids", default="", help="跨调用去重文件路径（每行一个 note_id）")
    parser.add_argument("--hyperlinks", action="store_true", help="启用超链接功能，生成 id_url_map.json")
    args = parser.parse_args()

    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]
    search_strategy = []
    if args.search_strategy:
        search_strategy = json.loads(args.search_strategy)
        if not isinstance(search_strategy, list):
            print("[!] search_strategy 必须是数组格式", flush=True)
            sys.exit(1)

    scraper = XHSScraper(
        max_posts=args.max_posts,
        search_strategy=search_strategy,
        seen_ids_path=args.seen_ids,
        hyperlinks=args.hyperlinks,
    )
    scraper.run(keywords=kws, output_file=args.output)
