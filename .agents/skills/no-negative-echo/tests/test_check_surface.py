from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "check_surface.py"


class CheckSurfaceTests(unittest.TestCase):
    def run_scan(self, term: str, content: str, filename: str = "artifact.txt") -> tuple[int, dict[str, object]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            terms = root / "terms.txt"
            surface = root / filename
            terms.write_text(term, encoding="utf-8")
            surface.write_text(content, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--terms-file", str(terms), "--root", str(root), str(surface)],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode, json.loads(result.stdout)

    def test_passes_accepted_surface(self) -> None:
        returncode, payload = self.run_scan("discarded-name", "accepted result")
        self.assertEqual(returncode, 0)
        self.assertEqual(payload["status"], "PASS")

    def test_reports_content_match_without_echoing_term(self) -> None:
        term = "discarded-name"
        returncode, payload = self.run_scan(term, f"mentions {term}")
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["status"], "FAIL")
        self.assertNotIn(term, json.dumps(payload))
        self.assertEqual(payload["failures"][0]["surfaces"], ["content"])

    def test_reports_path_match(self) -> None:
        returncode, payload = self.run_scan("discarded-name", "accepted result", "discarded-name.txt")
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["failures"][0]["surfaces"], ["relative_path"])

    def test_nfkc_and_casefold_match(self) -> None:
        returncode, payload = self.run_scan("redis", "ＲＥＤＩＳ")
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["status"], "FAIL")

    def test_marks_bidi_control_for_review(self) -> None:
        returncode, payload = self.run_scan("discarded-name", "accepted\u202eresult")
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["status"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
