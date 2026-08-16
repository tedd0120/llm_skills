import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_xhs import XHSScraper  # noqa: E402
from xhs_selectors import XHSSelectors as S  # noqa: E402


class FetchHelpersTest(unittest.TestCase):
    def test_search_relocates_card_by_href_after_masonry_reorder(self):
        target_href = "/search_result/note-a?xsec_token=token-a"

        class SnapshotLocator:
            def __init__(self, page):
                self.page = page

            def evaluate_all(self, expression):
                snapshot = list(self.page.card_hrefs)
                # 模拟读取 href 后，瀑布流在列表头部插入新卡片。
                self.page.card_hrefs.insert(0, "/search_result/note-new")
                return snapshot

        class IdentityLocator:
            def __init__(self, page, href):
                self.page = page
                self.href = href
                self.first = self

            def scroll_into_view_if_needed(self):
                pass

            def get_attribute(self, name):
                return self.href if name == "href" else None

            def click(self):
                self.page.clicked_hrefs.append(self.href)

        class FakePage:
            url = "https://www.xiaohongshu.com/search_result?keyword=test"

            def __init__(self):
                self.card_hrefs = [target_href, "/search_result/note-b"]
                self.clicked_hrefs = []

            def goto(self, url, wait_until=None):
                self.url = url

            def wait_for_selector(self, selector, **kwargs):
                pass

            def locator(self, selector):
                if selector == S.POST_LINK:
                    return SnapshotLocator(self)
                prefix = f"{S.POST_LINK}[href="
                self.assertTrue(selector.startswith(prefix) and selector.endswith("]"))
                href = json.loads(selector[len(prefix):-1])
                return IdentityLocator(self, href)

            @staticmethod
            def assertTrue(condition):
                if not condition:
                    raise AssertionError("unexpected locator selector")

        scraper = object.__new__(XHSScraper)
        scraper.speed_mode = True
        scraper.safe_mode = False
        scraper.dropped_id_mismatch = 0
        scraper._is_not_logged_in = lambda page: False
        scraper._do_sleep = lambda *args: None
        scraper._close_detail = lambda page: None
        scraper._extract_post_after_click = lambda *args: (
            {"post_id": "note-a", "title": "target"},
            "note-a",
            True,
        )

        page = FakePage()
        posts = scraper._search_keyword(page, "test", 1, set(), set())

        self.assertEqual(len(posts), 1)
        self.assertEqual(page.clicked_hrefs, [target_href])

    def test_speed_mode_keeps_ten_percent_delay(self):
        scraper = object.__new__(XHSScraper)
        scraper.speed_mode = True
        scraper.safe_mode = False

        with patch("fetch_xhs.random.uniform", return_value=4), \
                patch("fetch_xhs.time.sleep") as sleep:
            scraper._do_sleep(3, 8)

        sleep.assert_called_once_with(0.4)

    def test_close_detail_waits_for_hidden_even_in_speed_mode(self):
        class FakeLocator:
            first = None

            def __init__(self):
                self.first = self
                self.clicked = False

            def count(self):
                return 1

            def is_visible(self):
                return True

            def click(self):
                self.clicked = True

        class FakePage:
            def __init__(self):
                self.close_button = FakeLocator()
                self.waited = None

            def locator(self, selector):
                self.assert_selector = selector
                return self.close_button

            def wait_for_selector(self, selector, **kwargs):
                self.waited = (selector, kwargs)

        scraper = object.__new__(XHSScraper)
        scraper.speed_mode = True
        page = FakePage()

        scraper._close_detail(page)

        self.assertTrue(page.close_button.clicked)
        self.assertEqual(page.assert_selector, S.CLOSE_BUTTON)
        self.assertEqual(
            page.waited,
            (S.POST_DETAIL_CONTAINER, {"state": "hidden", "timeout": 5000}),
        )

    def test_note_id_comes_from_detail_url(self):
        self.assertEqual(
            XHSScraper._note_id_from_url("https://www.xiaohongshu.com/explore/abc123?x=1"),
            "abc123",
        )
        self.assertEqual(
            XHSScraper._note_id_from_url("https://www.xiaohongshu.com/search_result"),
            "",
        )

    def test_content_dedup_normalizes_whitespace_and_invisible_chars(self):
        posts = [
            {"author": "甲", "title": "同 一篇", "content": "正文\u200b内容"},
            {"author": "甲", "title": "同一篇", "content": "正文内容"},
            {"author": "乙", "title": "另一篇", "content": "正文内容"},
        ]
        unique, dropped = XHSScraper._deduplicate_posts(posts)
        self.assertEqual(len(unique), 2)
        self.assertEqual(dropped, 1)

    def test_counts_and_reply_prefix_are_normalized(self):
        self.assertEqual(XHSScraper._parse_int("1.2万"), 12000)
        self.assertEqual(XHSScraper._parse_int("2.5k"), 2500)
        self.assertEqual(XHSScraper._normalize_comment_text('\":\"回复内容'), ("回复内容", True))
        self.assertEqual(XHSScraper._normalize_comment_text("普通评论"), ("普通评论", False))

    def test_interaction_selectors_are_scoped_to_detail(self):
        for selector in (S.LIKE_COUNT, S.COLLECT_COUNT, S.COMMENT_COUNT, S.SHARE_COUNT):
            self.assertTrue(selector.startswith("#noteContainer "))

    def test_save_results_writes_unique_posts_and_dedup_stats(self):
        scraper = object.__new__(XHSScraper)
        scraper.search_strategy = []
        scraper.hyperlinks = False
        scraper.dropped_id_mismatch = 2
        posts = [
            {"author": "甲", "title": "同一篇", "content": "正文", "post_id": "a"},
            {"author": "甲", "title": "同 一篇", "content": "正 文", "post_id": "b"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "raw.json"
            scraper._save_results(posts, str(output), ["关键词"])
            data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(len(data["posts"]), 1)
        self.assertEqual(data["dedup"], {
            "posts_scraped": 2,
            "posts_unique": 1,
            "dropped_duplicate": 1,
            "dropped_id_mismatch": 2,
        })


if __name__ == "__main__":
    unittest.main()
