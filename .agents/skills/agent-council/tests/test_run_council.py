import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_council.py"
SPEC = importlib.util.spec_from_file_location("agent_council_runner", SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class AgentCouncilRunnerTests(unittest.TestCase):
    def test_main_report_path_must_be_fresh_and_outside_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            outside = Path(tmp) / "private" / "main.md"
            outside.parent.mkdir()

            self.assertEqual(
                RUNNER.prepare_main_report_path(str(outside), root),
                outside.resolve(),
            )

            with self.assertRaisesRegex(ValueError, "outside the workspace"):
                RUNNER.prepare_main_report_path(str(root / "main.md"), root)

            outside.write_text("stale report", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not exist"):
                RUNNER.prepare_main_report_path(str(outside), root)

    def test_select_reviewers_preserves_mixed_order_and_pi_substitutions(self):
        requested = [
            "claude:opus",
            "pi:openai-codex/missing",
            "pi:xai/grok-4.5",
        ]
        roster, failures = RUNNER.select_reviewers(
            requested,
            ["openai-codex/gpt-5.6-terra", "xai/grok-4.5"],
        )

        self.assertEqual(
            roster,
            [
                ("claude:opus", "claude:opus"),
                (
                    "pi:openai-codex/missing",
                    "pi:openai-codex/gpt-5.6-terra",
                ),
                ("pi:xai/grok-4.5", "pi:xai/grok-4.5"),
            ],
        )
        self.assertEqual(failures, [])

    def test_unavailable_backend_only_removes_its_reviewers(self):
        roster, failures = RUNNER.select_reviewers(
            [
                "pi:openai-codex/gpt-5.6-sol",
                "pi:xai/grok-4.5",
                "claude:opus",
            ],
            [
                "openai-codex/gpt-5.6-sol",
                "xai/grok-4.5",
            ],
            {"claude": "Claude command not found"},
        )

        self.assertEqual(
            roster,
            [
                (
                    "pi:openai-codex/gpt-5.6-sol",
                    "pi:openai-codex/gpt-5.6-sol",
                ),
                ("pi:xai/grok-4.5", "pi:xai/grok-4.5"),
            ],
        )
        self.assertEqual(
            failures,
            ["claude:opus: backend unavailable: Claude command not found"],
        )

    def test_claude_command_is_nonpersistent_and_read_only_when_enabled(self):
        disabled = RUNNER.build_claude_command(
            ["claude"], "opus", False, "high"
        )
        enabled = RUNNER.build_claude_command(
            ["claude"], "opus", True, "high"
        )

        for command in (disabled, enabled):
            self.assertIn("--safe-mode", command)
            self.assertIn("--no-session-persistence", command)
            self.assertIn("--disable-slash-commands", command)
            self.assertIn("--strict-mcp-config", command)
            self.assertIn("dontAsk", command)
            # The CLI rejects a bare "{}" — the object must carry mcpServers.
            mcp_config = command[command.index("--mcp-config") + 1]
            self.assertEqual(json.loads(mcp_config), {"mcpServers": {}})
        self.assertEqual(disabled[-1], "")
        self.assertEqual(enabled[-1], "Read,Grep,Glob")

    def test_main_report_is_created_during_calls_but_never_passed_to_reviewers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            brief = Path(tmp) / "brief.md"
            brief.write_text(
                "shared facts and evaluation dimensions", encoding="utf-8"
            )
            main_report = Path(tmp) / "private" / "main.md"
            main_report.parent.mkdir()
            secret = "MAIN_AGENT_PRIVATE_CONCLUSION_7f36"

            calls_started = threading.Event()
            release_calls = threading.Event()
            dispatched = []

            def fake_run_one(**kwargs):
                dispatched.append(dict(kwargs))
                calls_started.set()
                self.assertTrue(release_calls.wait(2))
                reviewer = kwargs["reviewer"]
                backend, model = RUNNER.parse_reviewer(reviewer)
                output = kwargs["reports_dir"] / RUNNER.safe_report_name(reviewer)
                output.write_text(f"# Report from {reviewer}\n", encoding="utf-8")
                return {
                    "reviewer": reviewer,
                    "backend": backend,
                    "model": model,
                    "ok": True,
                    "attempts": 1,
                    "seconds": 0.01,
                    "report": str(output),
                }

            def write_main_report():
                self.assertTrue(calls_started.wait(2))
                main_report.write_text(
                    f"# Main Agent Independent Report\n\n{secret}\n",
                    encoding="utf-8",
                )
                release_calls.set()

            writer = threading.Thread(target=write_main_report)
            writer.start()
            argv = [
                "run_council.py",
                "--topic",
                "isolation test",
                "--workspace",
                str(root),
                "--brief-file",
                str(brief),
                "--main-report-file",
                str(main_report),
                "--reviewer",
                "pi:provider-a/model-a",
                "--reviewer",
                "claude:opus",
                "--focus",
                "focus a",
                "--focus",
                "focus b",
            ]
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", argv),
                patch.object(
                    RUNNER, "resolve_workspace", return_value=(root, False)
                ),
                patch.object(
                    RUNNER, "resolve_pi_command", return_value=["pi"]
                ),
                patch.object(
                    RUNNER, "resolve_claude_command", return_value=["claude"]
                ),
                patch.object(
                    RUNNER,
                    "list_models",
                    return_value=["provider-a/model-a"],
                ),
                patch.object(RUNNER, "run_one", side_effect=fake_run_one),
                patch("sys.stdout", stdout),
            ):
                exit_code = RUNNER.main()
            writer.join(2)

            self.assertEqual(exit_code, 0)
            self.assertEqual(len(dispatched), 2)
            for call in dispatched:
                self.assertEqual(
                    call["brief"], brief.read_text(encoding="utf-8")
                )
                self.assertNotIn(secret, call["brief"])
                self.assertNotIn("main_report", call)

            summary = json.loads(stdout.getvalue().splitlines()[-1])
            recorded = Path(summary["main_agent_report"])
            self.assertEqual(
                recorded.read_text(encoding="utf-8").strip().splitlines()[-1],
                secret,
            )
            self.assertTrue(recorded.is_relative_to(root / ".agent-council"))
            self.assertEqual(
                summary["successful_reviewers"],
                ["pi:provider-a/model-a", "claude:opus"],
            )


if __name__ == "__main__":
    unittest.main()
