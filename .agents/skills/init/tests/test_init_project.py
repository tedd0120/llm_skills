from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / "scripts" / "init_project.py"
spec = importlib.util.spec_from_file_location("init_project", SCRIPT)
init_project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init_project)


def run(root: Path) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        init_project.init_project(root)
    return out.getvalue()


class InitProjectTests(unittest.TestCase):
    def test_new_project_uses_work_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run(root)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("## 工作区与产物目录", agents)
            self.assertIn(".work/<任务ID>/plan.md", agents)
            self.assertFalse((root / "docs" / "plans").exists())
            self.assertEqual(".work/\n.local/\n", (root / ".gitignore").read_text(encoding="utf-8"))

    def test_gitignore_rules_are_appended_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".gitignore").write_text("node_modules/\n.work\n", encoding="utf-8")
            run(root)
            run(root)
            self.assertEqual("node_modules/\n.work\n.local/\n", (root / ".gitignore").read_text(encoding="utf-8"))

    def test_legacy_layout_is_not_patched_with_conflicting_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Agent 指引\n\n## 规划\n\n- 计划写入 `docs/plans/`。\n", encoding="utf-8")
            output = run(root)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("workspace-layout", output)
            self.assertNotIn("## 工作区与产物目录", agents)
            self.assertIn("## Git 操作", agents)

    def test_existing_work_layout_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = (SCRIPT.parents[1] / "templates" / "AGENTS.md").read_text(encoding="utf-8")
            (root / "AGENTS.md").write_text(template, encoding="utf-8")
            self.assertIn("[完备]", run(root))


if __name__ == "__main__":
    unittest.main()
