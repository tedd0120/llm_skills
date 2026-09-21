from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).parents[1] / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scan_workspace = load("scan_workspace")
artifacts = load("artifacts")


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def write(root: Path, rel: str, text: str = "x") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ScanWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        git(self.root, "init", "-q")
        write(self.root, ".gitignore", "plans/\n.local/\nruns/*\n!runs/.gitkeep\n__pycache__/\n")
        write(self.root, "src/app.py", "OUT = '.tmp/report.txt'\n")
        write(self.root, "docs/plans/20260101_000000_design.md")
        write(self.root, "runs/.gitkeep", "")
        write(self.root, "AGENTS.md")
        git(self.root, "add", "-A")
        git(self.root, "add", "-f", "docs/plans/20260101_000000_design.md")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
        write(self.root, ".tmp/report.txt")
        write(self.root, "mystery/notes.txt")
        write(self.root, "tools/x/.local/state.json")
        write(self.root, "src/__pycache__/app.pyc")
        write(self.root, ".env", "SECRET=1")
        write(self.root, ".env.example", "SECRET=")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def entries(self) -> dict[str, dict]:
        return {e["path"]: e for e in scan_workspace.scan(self.root, full=False)["entries"]}

    def test_legacy_dir_is_migration_action_with_references(self) -> None:
        tmp = self.entries()[".tmp"]
        self.assertEqual("legacy", tmp["layer_guess"])
        self.assertEqual(1, tmp["untracked_unignored_files"])
        self.assertIn("src/app.py", tmp["referenced_by"])
        self.assertTrue(any("迁移到" in a for a in tmp["actions"]))
        self.assertTrue(any(".gitignore" in a for a in tmp["actions"]))

    def test_unknown_and_nested_local_raise_questions(self) -> None:
        found = self.entries()
        self.assertEqual("unknown", found["mystery"]["layer_guess"])
        self.assertTrue(found["mystery"]["questions"])
        self.assertTrue(found["tools/x/.local"]["questions"])

    def test_tracked_but_ignored_is_reported_and_reincluded_placeholder_is_not(self) -> None:
        report = scan_workspace.scan(self.root, full=False)
        self.assertEqual(["docs/plans/20260101_000000_design.md"], report["tracked_but_ignored"])
        found = {e["path"]: e for e in report["entries"]}
        self.assertTrue(any("命中忽略规则" in q for q in found["docs"]["questions"]))
        self.assertFalse(any("命中忽略规则" in q for q in found["runs"]["questions"]))

    def test_secret_and_template_split(self) -> None:
        found = self.entries()
        self.assertEqual("secret", found[".env"]["layer_guess"])
        self.assertEqual("asset", found[".env.example"]["layer_guess"])

    def test_ignored_nested_cache_is_omitted(self) -> None:
        self.assertNotIn("src/__pycache__", self.entries())

    def test_markdown_renders_every_entry(self) -> None:
        report = scan_workspace.scan(self.root, full=False)
        text = scan_workspace.to_markdown(report)
        for entry in report["entries"]:
            self.assertIn(f"`{entry['path']}`", text)


class ArtifactsTests(unittest.TestCase):
    TASK = ".work/20260921_110524_artifact-layout"

    def test_clean_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for name in ["scratch", "runner", "evidence"]:
                (root / self.TASK / name).mkdir(parents=True)
            (root / ".work/misc").mkdir()
            (root / ".tmp/old").mkdir(parents=True)
            with patch.object(artifacts, "active_users", return_value=[]):
                self.assertEqual(root / self.TASK, artifacts.validate(root, self.TASK))
                self.assertEqual(root / self.TASK / "scratch", artifacts.validate(root, f"{self.TASK}/scratch"))
                for bad in [".work", ".work/misc", f"{self.TASK}/evidence", ".tmp/old", "../outside", "."]:
                    with self.assertRaises(ValueError):
                        artifacts.validate(root, bad)
                with patch.object(artifacts, "active_users", return_value=[42]):
                    with self.assertRaises(ValueError):
                        artifacts.validate(root, self.TASK)

    def test_list_and_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / self.TASK / "scratch").mkdir(parents=True)
            write(root, f"{self.TASK}/scratch/log.txt", "abcd")
            (root / ".work/bad_name").mkdir()
            write(root, "docs/plans/old.md", "p")
            out = io.StringIO()
            with patch.object(artifacts, "active_users", return_value=[]), \
                    patch("sys.argv", ["artifacts.py", "list", "--root", str(root)]), redirect_stdout(out):
                artifacts.main()
            rows = {r["path"]: r for r in map(json.loads, out.getvalue().splitlines())}
            self.assertTrue(rows[self.TASK]["task_id_ok"])
            self.assertFalse(rows[".work/bad_name"]["task_id_ok"])
            self.assertTrue(rows["docs/plans"]["legacy"])
            with patch.object(artifacts, "active_users", return_value=[]), \
                    patch("sys.argv", ["artifacts.py", "clean", f"{self.TASK}/scratch", "--root", str(root), "--apply"]), \
                    redirect_stdout(io.StringIO()):
                artifacts.main()
            self.assertFalse((root / self.TASK / "scratch").exists())

    def test_task_id_format(self) -> None:
        for good in ["20260921_110524_artifact-layout", "20260918_164111_admin-management-center"]:
            self.assertIsNotNone(artifacts.TASK_ID.fullmatch(good))
        for bad in ["20260921_1105_x-y", "20260921_110524_layout", "20260921_110524_Artifact-Layout",
                    "20260921_110524_a_b", "20260921_110524_a-b-c-d-e-f"]:
            self.assertIsNone(artifacts.TASK_ID.fullmatch(bad))

    @unittest.skipUnless(Path("/proc").is_dir(), "需要 /proc")
    def test_live_process_cwd(self) -> None:
        self.assertIn(os.getpid(), artifacts.active_users(Path.cwd().resolve()))


if __name__ == "__main__":
    unittest.main()
