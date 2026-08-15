import sys
import json
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_xhs import XHSScraper  # noqa: E402
from xhs_selectors import XHSSelectors as S  # noqa: E402


class FetchHelpersTest(unittest.TestCase):
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
