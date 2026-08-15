import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_tasks.py"
SPEC = importlib.util.spec_from_file_location("verify_tasks", SCRIPT)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class VerifyRunTest(unittest.TestCase):
    def _make_run(self, report_body: str):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        tasks = root / "tasks.md"
        tasks.write_text("\n".join(f"- [x] 任务 {i}" for i in range(5)), encoding="utf-8")
        post = {
            "post_id": "abc",
            "url": "https://www.xiaohongshu.com/explore/abc",
            "card_url": "https://www.xiaohongshu.com/search_result/abc",
            "title": "标题",
            "content": "正文",
            "author": "作者",
            "comments_count": 1,
            "comments_captured": 1,
            "comments": [{"text": "评论", "author": "用户", "likes": 2, "is_reply": False}],
        }
        raw = {
            "dedup": {
                "posts_scraped": 1,
                "posts_unique": 1,
                "dropped_duplicate": 0,
                "dropped_id_mismatch": 0,
            },
            "posts": [post],
        }
        (root / "raw.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        report = root / "report.md"
        report.write_text(report_body, encoding="utf-8")
        return temp, tasks, report

    def test_valid_recommend_report_passes(self):
        body = """# 报告
## 搜索概览
| 数据规模 | 1 组独立内容 · 实际分析 1 条评论 · 来源页面累计 1 条 |
## 选购结论
| 定位 | 候选实体 |
|:--|:--|
| 首选 | A |
## 数据来源说明
说明
"""
        temp, tasks, report = self._make_run(body)
        try:
            self.assertEqual(VERIFY.verify_run(str(tasks), str(report), "recommend"), 0)
        finally:
            temp.cleanup()

    def test_missing_routed_section_is_rejected(self):
        body = """# 报告
## 搜索概览
| 数据规模 | 1 组独立内容 · 实际分析 1 条评论 · 来源页面累计 1 条 |
## 品牌声量
内容
## 数据来源说明
说明
"""
        temp, tasks, report = self._make_run(body)
        try:
            self.assertEqual(VERIFY.verify_run(str(tasks), str(report), "recommend"), 1)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
