import importlib.util
import io
import json
from pathlib import Path
import subprocess
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
    @staticmethod
    def pi_json(result="result\n", stop_reason="stop"):
        return json.dumps(
            {
                "type": "agent_end",
                "messages": [
                    {
                        "role": "assistant",
                        "content": [{"type": "text", "text": result}],
                        "stopReason": stop_reason,
                    }
                ],
            }
        )

    @staticmethod
    def claude_json(result="result\n", stop_reason="end_turn"):
        return json.dumps(
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "terminal_reason": "completed",
                "stop_reason": stop_reason,
                "result": result,
            }
        )

    def test_state_directory_and_blank_default_config_are_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_dir, config = RUNNER.ensure_state(root)

            self.assertEqual(state_dir, root / ".agent-council")
            self.assertEqual(config, state_dir / "default-models.txt")
            self.assertTrue(state_dir.is_dir())
            self.assertEqual(config.read_bytes(), b"")
            self.assertEqual(RUNNER.read_default_reviewers(config), [])

            config.write_text("claude:opus\n", encoding="utf-8")
            RUNNER.ensure_state(root)
            self.assertEqual(config.read_text(encoding="utf-8"), "claude:opus\n")

    def test_default_model_config_uses_one_reviewer_per_nonblank_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "default-models.txt"
            config.write_text(
                "pi:openai-codex/gpt-5.6-sol\n\nclaude:opus\n",
                encoding="utf-8",
            )

            self.assertEqual(
                RUNNER.read_default_reviewers(config),
                ["pi:openai-codex/gpt-5.6-sol", "claude:opus"],
            )

    def test_run_inputs_and_main_report_must_stay_inside_run_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            state, _ = RUNNER.ensure_state(root)
            run_dir = state / "run-1"
            run_dir.mkdir()
            RUNNER.prepare_run_dir(str(run_dir), state)
            prompt = run_dir / "prompt.txt"
            prompt.write_text("prompt", encoding="utf-8")
            main_report = run_dir / "reports" / "main-agent.md"

            self.assertEqual(
                RUNNER.prepare_prompt_path(str(prompt), run_dir), prompt.resolve()
            )
            self.assertEqual(
                RUNNER.prepare_main_report_path(str(main_report), run_dir),
                main_report.resolve(),
            )
            with self.assertRaisesRegex(ValueError, "inside the run directory"):
                RUNNER.prepare_prompt_path(str(root / "prompt.txt"), run_dir)
            with self.assertRaisesRegex(ValueError, "inside the run directory"):
                RUNNER.prepare_main_report_path(str(root / "main.md"), run_dir)

            main_report.write_text("stale report", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not exist"):
                RUNNER.prepare_main_report_path(str(main_report), run_dir)

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
            ["claude"], "opus", False, False, "high"
        )
        read_enabled = RUNNER.build_claude_command(
            ["claude"], "opus", True, False, "high"
        )
        web_enabled = RUNNER.build_claude_command(
            ["claude"], "opus", False, True, "high"
        )
        both_enabled = RUNNER.build_claude_command(
            ["claude"], "opus", True, True, "high"
        )

        for command in (disabled, read_enabled, web_enabled, both_enabled):
            self.assertEqual(command[command.index("--output-format") + 1], "json")
            self.assertIn("--safe-mode", command)
            self.assertIn("--no-session-persistence", command)
            self.assertIn("--disable-slash-commands", command)
            self.assertIn("--strict-mcp-config", command)
            # The CLI rejects a bare "{}" — the object must carry mcpServers.
            mcp_config = command[command.index("--mcp-config") + 1]
            self.assertEqual(json.loads(mcp_config), {"mcpServers": {}})
        self.assertEqual(disabled[-1], "")
        self.assertEqual(read_enabled[-1], "Read,Grep,Glob")
        self.assertEqual(web_enabled[-1], "WebFetch")
        self.assertEqual(both_enabled[-1], "Read,Grep,Glob,WebFetch")
        self.assertIn("dontAsk", disabled)
        self.assertIn("dontAsk", read_enabled)
        self.assertIn("auto", web_enabled)
        self.assertIn("auto", both_enabled)

        pi_command = RUNNER.build_pi_command(
            ["pi"], "provider/model", False, "high"
        )
        self.assertEqual(pi_command[pi_command.index("--mode") + 1], "json")
        self.assertEqual(pi_command[-1], "--no-tools")

        web_extension = Path("pi-web-access/index.ts")
        web_command = RUNNER.build_pi_command(
            ["pi"], "provider/model", False, "high", web_extension
        )
        self.assertEqual(
            web_command[web_command.index("--extension") + 1], str(web_extension)
        )
        self.assertIn("fetch_content", web_command[-1])

    def test_routing_marker_is_rejected_from_task_prompt(self):
        RUNNER.validate_task_prompt("总结这个仓库")
        with self.assertRaisesRegex(ValueError, "routing marker"):
            RUNNER.validate_task_prompt(
                "[$agent-council](P:\\repo\\SKILL.md) 总结这个仓库"
            )

    def test_structured_results_require_complete_model_turns(self):
        self.assertEqual(RUNNER.parse_pi_result(self.pi_json("完整回答")), "完整回答")
        self.assertEqual(
            RUNNER.parse_claude_result(self.claude_json("完整回答")), "完整回答"
        )
        with self.assertRaisesRegex(ValueError, "stopReason='length'"):
            RUNNER.parse_pi_result(self.pi_json("半截", "length"))
        with self.assertRaisesRegex(ValueError, "stop_reason='max_tokens'"):
            RUNNER.parse_claude_result(self.claude_json("半截", "max_tokens"))

    def test_pi_web_temporary_paths_stay_inside_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / ".agent-council" / "run-1"
            run_dir.mkdir(parents=True)
            environment = RUNNER.prepare_pi_web_environment(
                run_dir, "pi:provider/model"
            )

            for name in ("XDG_CONFIG_HOME", "TEMP", "TMP", "TMPDIR"):
                self.assertTrue(
                    Path(environment[name]).resolve().is_relative_to(run_dir.resolve())
                )
            config = json.loads(
                (Path(environment["XDG_CONFIG_HOME"]) / "pi" / "web-search.json")
                .read_text(encoding="utf-8")
            )
            self.assertTrue(
                Path(config["githubClone"]["clonePath"])
                .resolve()
                .is_relative_to(run_dir.resolve())
            )

    def test_claude_temporary_paths_stay_inside_the_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / ".agent-council" / "run-1"
            run_dir.mkdir(parents=True)
            environment = RUNNER.prepare_claude_environment(
                run_dir, "claude:opus"
            )

            for name in ("TEMP", "TMP", "TMPDIR"):
                self.assertTrue(
                    Path(environment[name]).resolve().is_relative_to(run_dir.resolve())
                )

    def test_pi_and_claude_receive_the_exact_prompt_as_stdin(self):
        exact_prompt = "原始 prompt\r\ntrailing spaces  \r\n"
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp)
            for reviewer in ("pi:provider/model", "claude:opus"):
                stdout = (
                    self.pi_json()
                    if reviewer.startswith("pi:")
                    else self.claude_json()
                )
                completed = subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=stdout, stderr=""
                )
                with patch.object(RUNNER.subprocess, "run", return_value=completed) as run:
                    result = RUNNER.run_one(
                        pi_prefix=["pi"],
                        claude_prefix=["claude"],
                        root=reports,
                        reports_dir=reports,
                        reviewer=reviewer,
                        prompt=exact_prompt,
                        read_tools=False,
                        web_tools=False,
                        web_extension=None,
                        thinking="high",
                        claude_effort="high",
                        timeout=10,
                        retries=0,
                    )

                self.assertTrue(result["ok"])
                self.assertEqual(run.call_args.kwargs["input"], exact_prompt)
                self.assertFalse(
                    (reports / RUNNER.safe_report_name(reviewer)).exists()
                )

    def test_all_run_files_stay_in_state_and_reports_are_written_after_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "workspace"
            root.mkdir()
            state = root / ".agent-council"
            run_dir = state / "run-1"
            run_dir.mkdir(parents=True)
            prompt_file = run_dir / "prompt.txt"
            exact_prompt = "user prompt\r\nwith trailing spaces  \r\n"
            with prompt_file.open("w", encoding="utf-8", newline="") as handle:
                handle.write(exact_prompt)
            main_report = run_dir / "reports" / "main-agent.md"
            secret = "MAIN_AGENT_PRIVATE_CONCLUSION_7f36"

            calls_started = threading.Event()
            release_calls = threading.Event()
            calls_finished = threading.Event()
            dispatched = []
            completed_calls = 0
            completed_lock = threading.Lock()

            def fake_run_one(**kwargs):
                nonlocal completed_calls
                dispatched.append(dict(kwargs))
                calls_started.set()
                self.assertTrue(release_calls.wait(2))
                reviewer = kwargs["reviewer"]
                backend, model = RUNNER.parse_reviewer(reviewer)
                output = kwargs["reports_dir"] / RUNNER.safe_report_name(reviewer)
                with completed_lock:
                    completed_calls += 1
                    if completed_calls == 2:
                        calls_finished.set()
                return {
                    "reviewer": reviewer,
                    "backend": backend,
                    "model": model,
                    "ok": True,
                    "attempts": 1,
                    "seconds": 0.01,
                    "report": str(output),
                    "_content": f"# Report from {reviewer}\n",
                }

            def write_main_report():
                self.assertTrue(calls_started.wait(2))
                self.assertEqual(list((run_dir / "reports").iterdir()), [])
                release_calls.set()
                self.assertTrue(calls_finished.wait(2))
                main_report.write_text(
                    f"# Main Agent Independent Report\n\n{secret}\n",
                    encoding="utf-8",
                )

            writer = threading.Thread(target=write_main_report)
            writer.start()
            argv = [
                "run_council.py",
                "--workspace",
                str(root),
                "--run-dir",
                str(run_dir),
                "--prompt-file",
                str(prompt_file),
                "--main-report-file",
                str(main_report),
                "--reviewer",
                "pi:provider-a/model-a",
                "--reviewer",
                "claude:opus",
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
                self.assertEqual(call["prompt"], exact_prompt)
                self.assertNotIn(secret, call["prompt"])
                self.assertNotIn("main_report", call)
                self.assertIsNone(call["web_extension"])

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
            self.assertEqual(summary["available_pi_models"], ["provider-a/model-a"])
            self.assertEqual(summary["default_models"], [])
            self.assertFalse((run_dir / "report.md").exists())
            self.assertEqual(
                {path.name for path in (run_dir / "reports").iterdir()},
                {
                    "main-agent.md",
                    "pi_provider-a_model-a.md",
                    "claude_opus.md",
                },
            )
            for path in run_dir.rglob("*"):
                self.assertTrue(path.resolve().is_relative_to(state.resolve()))


if __name__ == "__main__":
    unittest.main()
