#!/usr/bin/env python3
"""Run independent CLI-backed reviewers with the user's prompt unchanged."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Sequence


DEFAULT_MODELS_FILENAME = "default-models.txt"

PROVIDER_PREFERENCES = {
    "openai-codex": [
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.3-codex-spark",
    ],
    "xai": ["grok-4.5", "grok-4.3", "grok-build-0.1"],
    "kimi-coding": [
        "k3-256k",
        "k3",
        "kimi-for-coding",
        "kimi-for-coding-highspeed",
    ],
    "zai-coding-cn": [
        "glm-5.2",
        "glm-5.1",
        "glm-5-turbo",
        "glm-4.7",
        "glm-4.5-air",
    ],
}

DEFAULT_ATTEMPT_TIMEOUT_SECONDS = 60 * 60

CLAUDE_REVIEWER_SYSTEM_PROMPT = (
    "You are an independent reviewer. Complete the user task and return only the "
    "substantive final answer. Use only tools actually provided by the runtime. "
    "Never simulate, narrate, or print tool calls or tool outputs. If no tools are "
    "available, answer from the prompt alone. A preamble, plan, or tool transcript "
    "is not a final answer."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a multi-agent council through Pi and Claude CLIs."
    )
    parser.add_argument(
        "--workspace",
        default=".",
        help="Path used to resolve the Git root; defaults to the current directory.",
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Existing per-run directory directly under <workspace>/.agent-council/.",
    )
    parser.add_argument(
        "--prompt-file",
        required=True,
        help="UTF-8 file containing the user's prompt verbatim.",
    )
    parser.add_argument(
        "--main-report-file",
        required=True,
        help=(
            "Path where the main agent will atomically write its independent UTF-8 "
            "report while reviewers run. The runner reads it only after all calls finish."
        ),
    )
    parser.add_argument(
        "--reviewer",
        action="append",
        dest="reviewers",
        help=(
            "Requested backend:model, such as pi:provider/model or claude:opus. "
            "Repeat to override the default roster."
        ),
    )
    parser.add_argument(
        "--read-tools",
        action="store_true",
        default=True,
        help=(
            "Allow Pi read,grep,find,ls and Claude Read,Grep,Glob tools "
            "(enabled by default). This is not a path sandbox."
        ),
    )
    parser.add_argument(
        "--web-tools",
        action="store_true",
        help=(
            "Load pi-web-access for Pi reviewers and allow WebFetch for Claude "
            "reviewers."
        ),
    )
    parser.add_argument(
        "--thinking",
        default="high",
        help=(
            "Pi thinking level for every Pi reviewer: "
            "off, minimal, low, medium, high, xhigh, max (default: high)."
        ),
    )
    parser.add_argument(
        "--claude-effort",
        default="high",
        help=(
            "Claude effort level: low, medium, high, xhigh, max "
            "(default: high)."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_ATTEMPT_TIMEOUT_SECONDS,
        help=(
            "Per-attempt timeout in seconds "
            f"(default: {DEFAULT_ATTEMPT_TIMEOUT_SECONDS})."
        ),
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Retries after a failed, timed-out, or empty call (default: 1).",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=5,
        help="Maximum simultaneous reviewer calls (default: 5).",
    )
    parser.add_argument(
        "--pi-command",
        default="pi",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--claude-command",
        default="claude",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--available-claude-model",
        action="append",
        dest="available_claude_models",
        default=[],
        help=(
            "Claude model ID captured from the live `/model` picker before user "
            "confirmation. Repeat for every displayed option."
        ),
    )
    return parser.parse_args()


def parse_reviewer(value: str) -> tuple[str, str]:
    backend, separator, model = value.partition(":")
    if not separator or not backend or not model:
        raise ValueError(
            f"invalid reviewer {value!r}: expected pi:provider/model or claude:model"
        )
    if backend not in {"pi", "claude"}:
        raise ValueError(f"unsupported reviewer backend {backend!r} in {value!r}")
    if backend == "pi" and "/" not in model:
        raise ValueError(f"invalid Pi reviewer {value!r}: expected pi:provider/model")
    return backend, model


def validate_args(args: argparse.Namespace, requested: Sequence[str]) -> None:
    if args.timeout < 1:
        raise ValueError("--timeout must be at least 1 second")
    if args.retries < 0:
        raise ValueError("--retries cannot be negative")
    if args.max_parallel < 1:
        raise ValueError("--max-parallel must be at least 1")
    if len(set(requested)) != len(requested):
        raise ValueError("duplicate --reviewer values are not allowed")
    for reviewer in requested:
        parse_reviewer(reviewer)
    requested_count = len(requested)
    if requested_count < 2:
        raise ValueError("Agent Council requires at least two requested reviewers")
    if args.claude_effort not in {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("--claude-effort must be one of: low, medium, high, xhigh, max")


def read_utf8_exact(path_text: str, label: str) -> str:
    path = Path(path_text).expanduser().resolve()
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            value = handle.read()
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read {label} as UTF-8: {path}: {exc}") from exc
    if not value.strip():
        raise ValueError(f"{label} is empty: {path}")
    return value


SKILL_INVOCATION = re.compile(
    r"^(?:\[\$agent-council\]\([^\r\n]*\)|\$agent-council)(?:[ \t]+|(?=\r?$))",
    re.IGNORECASE,
)


def validate_task_prompt(prompt: str) -> None:
    if SKILL_INVOCATION.match(prompt):
        raise ValueError(
            "prompt file starts with the agent-council routing marker; write only the user task"
        )


def require_inside_run(path: Path, run_dir: Path, label: str) -> None:
    try:
        path.relative_to(run_dir)
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside the run directory: {run_dir}") from exc


def prepare_run_dir(path_text: str, state_dir: Path) -> Path:
    path = Path(path_text).expanduser().resolve()
    try:
        relative = path.relative_to(state_dir)
    except ValueError as exc:
        raise ValueError(f"run directory must stay inside {state_dir}") from exc
    if len(relative.parts) != 1:
        raise ValueError(f"run directory must be a direct child of {state_dir}: {path}")
    if not path.is_dir():
        raise ValueError(f"run directory does not exist: {path}")
    reports = path / "reports"
    if reports.exists():
        raise ValueError(f"reports directory must not exist before runner starts: {reports}")
    reports.mkdir()
    return path


def prepare_prompt_path(path_text: str, run_dir: Path) -> Path:
    path = Path(path_text).expanduser().resolve()
    require_inside_run(path, run_dir, "prompt file")
    if not path.is_file():
        raise ValueError(f"prompt file does not exist: {path}")
    return path


def prepare_main_report_path(path_text: str, run_dir: Path) -> Path:
    """Validate a fresh report path inside this run's reports directory."""
    path = Path(path_text).expanduser().resolve()
    require_inside_run(path, run_dir, "main-agent report path")
    if path.parent != run_dir / "reports":
        raise ValueError(
            f"main-agent report path must be directly inside {run_dir / 'reports'}"
        )
    if path.exists():
        raise ValueError(
            f"main-agent report path must not exist before reviewer dispatch: {path}"
        )
    if not path.parent.is_dir():
        raise ValueError(f"main-agent report parent directory does not exist: {path.parent}")
    return path


def wait_for_main_report(path: Path, timeout: int) -> str:
    """Wait for the independently produced report after every Pi call has finished."""
    deadline = time.monotonic() + timeout
    while True:
        if path.exists():
            try:
                value = path.read_text(encoding="utf-8")
            except UnicodeError as exc:
                raise ValueError(f"main-agent report is not valid UTF-8: {path}: {exc}") from exc
            except OSError:
                value = ""
            if value.strip():
                return value.rstrip()
        if time.monotonic() >= deadline:
            raise ValueError(
                f"main-agent report was not completed within {timeout}s after reviewer calls: {path}"
            )
        time.sleep(0.1)


def resolve_workspace(start_text: str) -> tuple[Path, bool]:
    start = Path(start_text).expanduser().resolve()
    if not start.exists():
        raise ValueError(f"workspace does not exist: {start}")
    if start.is_file():
        start = start.parent

    git = shutil.which("git")
    if git:
        probe = subprocess.run(
            [git, "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
        if probe.returncode == 0 and probe.stdout.strip():
            return Path(probe.stdout.strip()).resolve(), True
    return start, False


def ensure_gitignore(root: Path, is_git: bool) -> str | None:
    """Add .agent-council/ to the root .gitignore; return a warning instead of raising."""
    if not is_git:
        return None
    path = root / ".gitignore"
    manual_hint = "add '.agent-council/' to it manually"
    existing = ""
    had_bom = False
    if path.exists():
        try:
            raw = path.read_bytes()
        except OSError as exc:
            return f".gitignore not updated ({exc}); {manual_hint}"
        had_bom = raw.startswith(b"\xef\xbb\xbf")
        try:
            existing = raw.decode("utf-8-sig")
        except UnicodeError:
            return f".gitignore not updated (not valid UTF-8); {manual_hint}"
    rule = re.compile(r"^\s*/?\.agent-council/?\s*$")
    if any(rule.match(line) for line in existing.splitlines()):
        return None
    # newline="" — text-mode translation would rewrite \r\n as \r\r\n, and git
    # then reads the pattern with a trailing \r that matches nothing.
    eol = "\r\n" if "\r\n" in existing else "\n"
    prefix = "" if not existing or existing.endswith(("\n", "\r")) else eol
    try:
        encoding = "utf-8-sig" if had_bom else "utf-8"
        with path.open("w", encoding=encoding, newline="") as handle:
            handle.write(existing + prefix + ".agent-council/" + eol)
    except OSError as exc:
        return f".gitignore not updated ({exc}); {manual_hint}"
    return None


def ensure_state(root: Path) -> tuple[Path, Path]:
    base = root / ".agent-council"
    base.mkdir(parents=True, exist_ok=True)
    config = base / DEFAULT_MODELS_FILENAME
    config.touch(exist_ok=True)
    return base, config


def read_default_reviewers(config: Path) -> list[str]:
    """Read one backend:model ID per nonblank line from the user-owned config."""
    try:
        with config.open("r", encoding="utf-8", newline="") as handle:
            return [line.strip() for line in handle if line.strip()]
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read default model config as UTF-8: {config}: {exc}") from exc


def write_default_reviewers(config: Path, reviewers: Sequence[str]) -> None:
    """Atomically replace the default roster with verified reviewer IDs."""
    content = "".join(f"{reviewer}\n" for reviewer in reviewers)
    temporary = config.with_name(config.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, config)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ValueError(f"cannot update default model config: {config}: {exc}") from exc


def persist_verified_manual_roster(
    config: Path,
    manual_override: bool,
    results: Sequence[dict[str, object]],
) -> list[str] | None:
    if not manual_override:
        return None
    verified = [str(item["reviewer"]) for item in results if item["ok"]]
    if len(verified) < 2:
        return None
    write_default_reviewers(config, verified)
    return verified


def resolve_command(command_text: str, label: str) -> list[str]:
    expanded = str(Path(command_text).expanduser()) if any(
        separator in command_text for separator in (os.sep, os.altsep) if separator
    ) else command_text
    resolved = shutil.which(expanded)
    if not resolved and Path(expanded).exists():
        resolved = str(Path(expanded).resolve())
    if not resolved:
        raise ValueError(f"{label} command not found: {command_text}")

    suffix = Path(resolved).suffix.lower()
    if suffix == ".py":
        return [sys.executable, resolved]
    if os.name == "nt" and suffix in {".cmd", ".bat"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/s", "/c", resolved]
    return [resolved]


def resolve_pi_command(command_text: str) -> list[str]:
    return resolve_command(command_text, "Pi")


def resolve_claude_command(command_text: str) -> list[str]:
    return resolve_command(command_text, "Claude")


def list_models(pi_prefix: Sequence[str], root: Path) -> list[str]:
    command = [*pi_prefix, "--list-models"]
    process = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise ValueError(f"`pi --list-models` failed: {detail or 'no error output'}")

    found: list[str] = []
    for line in process.stdout.splitlines():
        columns = line.split()
        if len(columns) < 2 or columns[0].lower() == "provider":
            continue
        if set(columns[0]) == {"-"}:
            continue
        candidate = f"{columns[0]}/{columns[1]}"
        if candidate not in found:
            found.append(candidate)
    if not found:
        raise ValueError("`pi --list-models` returned no parseable models")
    return found


def resolve_pi_web_extension(pi_prefix: Sequence[str], root: Path) -> Path:
    process = subprocess.run(
        [*pi_prefix, "list"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise ValueError(f"`pi list` failed: {detail or 'no error output'}")

    lines = process.stdout.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "npm:pi-web-access":
            continue
        for path_line in lines[index + 1 :]:
            if path_line.strip().startswith("npm:"):
                break
            if not path_line.strip():
                continue
            candidate = Path(path_line.strip()).expanduser().resolve() / "index.ts"
            if candidate.is_file():
                return candidate
            break
    raise ValueError("Pi package pi-web-access is not installed")


def select_models(
    requested: Sequence[str], available: Sequence[str]
) -> tuple[list[tuple[str, str]], list[str]]:
    available_set = set(available)
    selected: list[tuple[str, str]] = []
    used: set[str] = set()
    failures: list[str] = []

    for model in requested:
        if "/" not in model:
            failures.append(f"{model}: expected provider/model")
            continue
        provider, _ = model.split("/", 1)
        actual = model if model in available_set and model not in used else None

        if actual is None:
            ordered = [
                f"{provider}/{name}" for name in PROVIDER_PREFERENCES.get(provider, [])
            ]
            ordered.extend(
                sorted(item for item in available if item.startswith(provider + "/"))
            )
            actual = next(
                (item for item in ordered if item in available_set and item not in used),
                None,
            )

        if actual is None:
            failures.append(f"{model}: no available unused model from provider {provider}")
            continue
        selected.append((model, actual))
        used.add(actual)

    return selected, failures


def select_reviewers(
    requested: Sequence[str],
    available_pi_models: Sequence[str],
    unavailable_backends: dict[str, str] | None = None,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Resolve requested reviewer IDs to actual backend:model IDs."""
    unavailable_backends = unavailable_backends or {}
    pi_requested = [
        model for reviewer in requested
        for backend, model in [parse_reviewer(reviewer)]
        if backend == "pi" and backend not in unavailable_backends
    ]
    selected_pi, failures = select_models(pi_requested, available_pi_models)
    pi_by_requested = {
        f"pi:{requested_model}": f"pi:{actual_model}"
        for requested_model, actual_model in selected_pi
    }
    failure_by_model = {
        item.split(":", 1)[0]: item for item in failures
    }

    roster: list[tuple[str, str]] = []
    selection_failures: list[str] = []
    for reviewer in requested:
        backend, model = parse_reviewer(reviewer)
        if backend in unavailable_backends:
            selection_failures.append(
                f"{reviewer}: backend unavailable: {unavailable_backends[backend]}"
            )
            continue
        if backend == "claude":
            roster.append((reviewer, reviewer))
            continue
        actual = pi_by_requested.get(reviewer)
        if actual:
            roster.append((reviewer, actual))
        else:
            selection_failures.append(
                f"{reviewer}: {failure_by_model.get(model, 'no valid Pi model')}"
            )
    return roster, selection_failures


def safe_report_name(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("._") + ".md"


SUMMARY_ERROR_LIMIT = 500


def as_text(value: object) -> str:
    """TimeoutExpired.stdout/.stderr may be bytes even when the call used text mode."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value) if value else ""


def truncate_error(text: str, limit: int = SUMMARY_ERROR_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"… [+{len(text) - limit} chars; full record in the report file]"


def build_pi_command(
    pi_prefix: Sequence[str],
    model: str,
    read_tools: bool,
    thinking: str,
    web_extension: Path | None = None,
) -> list[str]:
    command = [
        *pi_prefix,
        "-p",
        "--mode",
        "json",
        "--no-session",
        "--model",
        model,
        "--thinking",
        thinking,
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--no-context-files",
    ]
    tools = ["read", "grep", "find", "ls"] if read_tools else []
    if web_extension:
        command.extend(["--extension", str(web_extension)])
        tools.extend(
            ["web_search", "source_check", "fetch_content", "get_search_content"]
        )
    if tools:
        command.extend(["--tools", ",".join(tools)])
    else:
        command.append("--no-tools")
    return command


def build_claude_command(
    claude_prefix: Sequence[str],
    model: str,
    read_tools: bool,
    web_tools: bool,
    effort: str,
) -> list[str]:
    tools = ["Read", "Grep", "Glob"] if read_tools else []
    if web_tools:
        tools.append("WebFetch")
    return [
        *claude_prefix,
        "--print",
        "--output-format",
        "json",
        "--model",
        model,
        "--effort",
        effort,
        "--safe-mode",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--permission-mode",
        "auto" if web_tools else "dontAsk",
        "--tools",
        ",".join(tools),
        "--system-prompt",
        CLAUDE_REVIEWER_SYSTEM_PROMPT,
    ]


def parse_pi_result(raw: str) -> str:
    events = []
    try:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        raise ValueError(f"Pi returned invalid JSONL: {exc}") from exc
    agent_end = next(
        (event for event in reversed(events) if event.get("type") == "agent_end"),
        None,
    )
    if not agent_end:
        raise ValueError("Pi response has no agent_end event")
    assistants = [
        message
        for message in agent_end.get("messages", [])
        if message.get("role") == "assistant"
    ]
    if not assistants:
        raise ValueError("Pi response has no assistant message")
    final = assistants[-1]
    stop_reason = final.get("stopReason")
    if stop_reason != "stop":
        raise ValueError(f"Pi response ended with stopReason={stop_reason!r}")
    text_parts = [
        item.get("text", "")
        for item in final.get("content", [])
        if item.get("type") == "text"
    ]
    result = "".join(text_parts)
    if not result.strip():
        raise ValueError("Pi final response is empty")
    return result


def parse_claude_result(raw: str) -> str:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned invalid JSON: {exc}") from exc
    if (
        payload.get("is_error")
        or payload.get("subtype") != "success"
        or payload.get("terminal_reason") != "completed"
        or payload.get("stop_reason") != "end_turn"
    ):
        raise ValueError(
            "Claude response ended incompletely: "
            f"subtype={payload.get('subtype')!r}, "
            f"terminal_reason={payload.get('terminal_reason')!r}, "
            f"stop_reason={payload.get('stop_reason')!r}"
        )
    result = payload.get("result", "")
    if not isinstance(result, str) or not result.strip():
        raise ValueError("Claude final response is empty")
    return result


def prepare_pi_web_environment(run_dir: Path, reviewer: str) -> dict[str, str]:
    web_state = run_dir / "pi-web" / safe_report_name(reviewer)[:-3]
    config_dir = web_state / "pi"
    temp_dir = web_state / "tmp"
    config_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
    (config_dir / "web-search.json").write_text(
        json.dumps(
            {
                "workflow": "none",
                "githubClone": {"clonePath": str(web_state / "github-repos")},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    process_env = os.environ.copy()
    process_env.update(
        {
            "XDG_CONFIG_HOME": str(web_state),
            "TEMP": str(temp_dir),
            "TMP": str(temp_dir),
            "TMPDIR": str(temp_dir),
        }
    )
    return process_env


def prepare_claude_environment(run_dir: Path, reviewer: str) -> dict[str, str]:
    temp_dir = run_dir / "claude-temp" / safe_report_name(reviewer)[:-3]
    temp_dir.mkdir(parents=True, exist_ok=True)
    process_env = os.environ.copy()
    process_env.update(
        {
            "TEMP": str(temp_dir),
            "TMP": str(temp_dir),
            "TMPDIR": str(temp_dir),
        }
    )
    return process_env


def run_one(
    *,
    pi_prefix: Sequence[str] | None,
    claude_prefix: Sequence[str] | None,
    root: Path,
    reports_dir: Path,
    reviewer: str,
    prompt: str,
    read_tools: bool,
    web_tools: bool,
    web_extension: Path | None,
    thinking: str,
    claude_effort: str,
    timeout: int,
    retries: int,
) -> dict[str, object]:
    backend, model = parse_reviewer(reviewer)
    if backend == "pi":
        if pi_prefix is None:
            raise ValueError("Pi command was not resolved")
        command = build_pi_command(
            pi_prefix, model, read_tools, thinking, web_extension
        )
    else:
        if claude_prefix is None:
            raise ValueError("Claude command was not resolved")
        command = build_claude_command(
            claude_prefix, model, read_tools, web_tools, claude_effort
        )
    output_path = reports_dir / safe_report_name(reviewer)
    errors: list[str] = []
    started = time.monotonic()

    for attempt in range(1, retries + 2):
        try:
            process_env = None
            if backend == "pi" and web_extension:
                process_env = prepare_pi_web_environment(
                    reports_dir.parent, reviewer
                )
            elif backend == "claude":
                process_env = prepare_claude_environment(
                    reports_dir.parent, reviewer
                )
            process = subprocess.run(
                command,
                cwd=root,
                input=prompt,
                env=process_env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW")
                    else 0
                ),
            )
            stdout = process.stdout or ""
            stderr = process.stderr or ""
            if process.returncode == 0 and stdout.strip():
                try:
                    content = (
                        parse_pi_result(stdout)
                        if backend == "pi"
                        else parse_claude_result(stdout)
                    )
                except ValueError as exc:
                    errors.append(
                        f"Attempt {attempt}: {exc}; raw stdout={stdout}; "
                        f"stderr={stderr.strip() or '<empty>'}"
                    )
                    continue
                return {
                    "reviewer": reviewer,
                    "backend": backend,
                    "model": model,
                    "ok": True,
                    "attempts": attempt,
                    "seconds": round(time.monotonic() - started, 2),
                    "report": str(output_path),
                    "_content": content,
                }
            errors.append(
                f"Attempt {attempt}: exit={process.returncode}; "
                f"stdout={stdout.strip() or '<empty>'}; "
                f"stderr={stderr.strip() or '<empty>'}"
            )
        except subprocess.TimeoutExpired as exc:
            errors.append(
                f"Attempt {attempt}: timed out after {timeout}s; "
                f"partial stdout={as_text(exc.stdout).strip() or '<empty>'}; "
                f"partial stderr={as_text(exc.stderr).strip() or '<empty>'}"
            )
        except OSError as exc:
            errors.append(
                f"Attempt {attempt}: could not launch {backend} reviewer: {exc}"
            )

    failure_text = (
        "# Agent Council Call Failed\n\n"
        f"- Reviewer: `{reviewer}`\n"
        f"- Backend: `{backend}`\n"
        f"- Model: `{model}`\n"
        f"- Attempts: {retries + 1}\n\n"
        "## Raw error record\n\n"
        + "\n\n".join(errors)
        + "\n"
    )
    return {
        "reviewer": reviewer,
        "backend": backend,
        "model": model,
        "ok": False,
        "attempts": retries + 1,
        "seconds": round(time.monotonic() - started, 2),
        "report": str(output_path),
        "_content": failure_text,
        "error": truncate_error(errors[-1]) if errors else "unknown failure",
    }


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def write_input(
    *,
    path: Path,
    root: Path,
    config: Path,
    default_reviewers: Sequence[str],
    available_pi_models: Sequence[str],
    available_claude_models: Sequence[str],
    persisted_default_reviewers: Sequence[str] | None,
    requested: Sequence[str],
    roster: Sequence[tuple[str, str]],
    selection_failures: Sequence[str],
    read_tools: bool,
    web_tools: bool,
    thinking: str,
    claude_effort: str,
    timeout: int,
    retries: int,
    prompt: str,
    main_report_recorded: bool,
) -> None:
    rows = []
    for requested_reviewer, actual_reviewer in roster:
        rows.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(requested_reviewer),
                    markdown_cell(actual_reviewer),
                ]
            )
            + " |"
        )
    roster_table = "\n".join(rows) or "| _none_ | _none_ |"
    selection_text = (
        "\n".join(f"- {item}" for item in selection_failures) if selection_failures else "- None"
    )
    default_text = "\n".join(f"- `{item}`" for item in default_reviewers) or "- _none_"
    available_pi_text = "\n".join(f"- `{item}`" for item in available_pi_models) or "- _none_"
    available_claude_text = (
        "\n".join(f"- `{item}`" for item in available_claude_models) or "- _none recorded_"
    )
    persisted_text = (
        "\n".join(f"- `{item}`" for item in persisted_default_reviewers)
        if persisted_default_reviewers is not None
        else "- _unchanged_"
    )
    content = f"""\
# Agent Council Input

- Created: {dt.datetime.now().astimezone().isoformat(timespec="seconds")}
- Workspace root: `{root}`
- Default model config: `{config}`
- Pi thinking: `{thinking}`
- Claude effort: `{claude_effort}`
- File tools: `{"Pi read,grep,find,ls; Claude Read,Grep,Glob" if read_tools else "disabled"}`
- Web tools: `{"Pi web_search,source_check,fetch_content,get_search_content; Claude WebFetch" if web_tools else "disabled"}`
- Per-attempt timeout: `{timeout}s`
- Retries after first attempt: `{retries}`
- Main-agent report: `{"reports/main-agent.md" if main_report_recorded else "not collected"}`

## Reviewer roster

| Requested | Actual |
|---|---|
{roster_table}

## Configured default models

{default_text}

## Pi models reported by `pi --list-models`

{available_pi_text}

## Claude models captured from the live `/model` picker

{available_claude_text}

## Verified models persisted as defaults

{persisted_text}

## Selection failures

{selection_text}

## User prompt sent to every reviewer verbatim

{prompt}

## Main-agent independence

The main agent performs the same task while reviewer calls are in flight. Its report is
written to this run's reports directory only after every reviewer call has finished, and
is never included in any reviewer prompt.
"""
    path.write_text(content, encoding="utf-8")


def emit_summary(
    run_dir: Path | None,
    status: str,
    warnings: Sequence[str] = (),
    **details: object,
) -> None:
    payload: dict[str, object] = {
        "status": status,
        "run_dir": str(run_dir) if run_dir else None,
    }
    if warnings:
        payload["warnings"] = list(warnings)
    payload.update(details)
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    # Force UTF-8 so the final JSON summary survives Windows pipes (GBK/cp1252).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass

    args = parse_args()
    run_dir: Path | None = None
    warnings: list[str] = []
    config_path: Path | None = None
    default_reviewers: list[str] = []
    available_pi_models: list[str] = []
    available_claude_models: list[str] = list(args.available_claude_models)
    persisted_default_reviewers: list[str] | None = None
    web_extension: Path | None = None

    try:
        root, is_git = resolve_workspace(args.workspace)
        state_dir, config_path = ensure_state(root)
        default_reviewers = read_default_reviewers(config_path)
        gitignore_warning = ensure_gitignore(root, is_git)
        if gitignore_warning:
            warnings.append(gitignore_warning)
            print(
                f"[agent-council] warning: {gitignore_warning}",
                file=sys.stderr,
                flush=True,
            )
        backend_failures: dict[str, str] = {}
        pi_prefix: list[str] | None = None
        claude_prefix: list[str] | None = None
        try:
            pi_prefix = resolve_pi_command(args.pi_command)
            available_pi_models = list_models(pi_prefix, root)
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            backend_failures["pi"] = str(exc)

        print(
            "[agent-council] configured default models: "
            + (", ".join(default_reviewers) if default_reviewers else "<none>"),
            file=sys.stderr,
            flush=True,
        )
        print(
            "[agent-council] Pi models from `pi --list-models`: "
            + (", ".join(available_pi_models) if available_pi_models else "<unavailable>"),
            file=sys.stderr,
            flush=True,
        )
        print(
            "[agent-council] Claude models from the live `/model` picker: "
            + (", ".join(available_claude_models) if available_claude_models else "<none recorded>"),
            file=sys.stderr,
            flush=True,
        )

        requested = (
            list(args.reviewers)
            if args.reviewers is not None
            else list(default_reviewers)
        )
        validate_args(args, requested)
        run_dir = prepare_run_dir(args.run_dir, state_dir)
        prompt_path = prepare_prompt_path(args.prompt_file, run_dir)
        prompt = read_utf8_exact(str(prompt_path), "prompt file")
        validate_task_prompt(prompt)
        main_report_path = prepare_main_report_path(args.main_report_file, run_dir)

        requested_backends = {parse_reviewer(item)[0] for item in requested}
        if args.web_tools and "pi" in requested_backends:
            if pi_prefix is None:
                raise ValueError(
                    f"Pi web tools require an available Pi CLI: {backend_failures.get('pi')}"
                )
            web_extension = resolve_pi_web_extension(pi_prefix, root)
        if "claude" in requested_backends:
            try:
                claude_prefix = resolve_claude_command(args.claude_command)
            except (ValueError, OSError, subprocess.SubprocessError) as exc:
                backend_failures["claude"] = str(exc)
        roster, selection_failures = select_reviewers(
            requested, available_pi_models, backend_failures
        )

        if len(roster) < 2:
            write_input(
                path=run_dir / "input.md",
                root=root,
                config=config_path,
                default_reviewers=default_reviewers,
                available_pi_models=available_pi_models,
                available_claude_models=available_claude_models,
                persisted_default_reviewers=persisted_default_reviewers,
                requested=requested,
                roster=roster,
                selection_failures=selection_failures,
                read_tools=args.read_tools,
                web_tools=args.web_tools,
                thinking=args.thinking,
                claude_effort=args.claude_effort,
                timeout=args.timeout,
                retries=args.retries,
                prompt=prompt,
                main_report_recorded=False,
            )
            emit_summary(
                run_dir,
                "aborted",
                warnings=warnings,
                reason="fewer than two valid reviewers",
                selection_failures=selection_failures,
                default_models=default_reviewers,
                available_pi_models=available_pi_models,
                available_claude_models=available_claude_models,
                default_models_config=str(config_path),
            )
            return 3

        workers = min(args.max_parallel, len(roster))
        results: list[dict[str, object]] = []
        reports_dir = run_dir / "reports"
        print(
            f"[agent-council] calling {len(roster)} reviewers, "
            f"timeout {args.timeout}s/attempt, Pi thinking {args.thinking}, "
            f"Claude effort {args.claude_effort}",
            file=sys.stderr,
            flush=True,
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    run_one,
                    pi_prefix=pi_prefix,
                    claude_prefix=claude_prefix,
                    root=root,
                    reports_dir=reports_dir,
                    reviewer=actual,
                    prompt=prompt,
                    read_tools=args.read_tools,
                    web_tools=args.web_tools,
                    web_extension=web_extension,
                    thinking=args.thinking,
                    claude_effort=args.claude_effort,
                    timeout=args.timeout,
                    retries=args.retries,
                )
                for _, actual in roster
            ]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                print(
                    f"[agent-council] {result['reviewer']}: "
                    f"{'ok' if result['ok'] else 'FAILED'} "
                    f"after {result['seconds']}s ({len(results)}/{len(roster)})",
                    file=sys.stderr,
                    flush=True,
                )
        for result in results:
            Path(str(result["report"])).write_text(
                str(result.pop("_content")), encoding="utf-8"
            )

        order = {actual: index for index, (_, actual) in enumerate(roster)}
        results.sort(key=lambda item: order.get(str(item["reviewer"]), len(order)))
        succeeded = [item for item in results if item["ok"]]
        failed = [item for item in results if not item["ok"]]
        status = "ready" if len(succeeded) >= 2 else "aborted"
        persisted_default_reviewers = persist_verified_manual_roster(
            config_path,
            args.reviewers is not None,
            results,
        )
        if persisted_default_reviewers is not None:
            print(
                "[agent-council] verified manual reviewer roster saved to "
                f"{config_path}: {', '.join(persisted_default_reviewers)}",
                file=sys.stderr,
                flush=True,
            )

        print(
            "[agent-council] reviewer calls complete; collecting the frozen independent "
            "main-agent report",
            file=sys.stderr,
            flush=True,
        )
        main_report = wait_for_main_report(main_report_path, args.timeout)
        main_report_target = main_report_path

        write_input(
            path=run_dir / "input.md",
            root=root,
            config=config_path,
            default_reviewers=default_reviewers,
            available_pi_models=available_pi_models,
            available_claude_models=available_claude_models,
            persisted_default_reviewers=persisted_default_reviewers,
            requested=requested,
            roster=roster,
            selection_failures=selection_failures,
            read_tools=args.read_tools,
            web_tools=args.web_tools,
            thinking=args.thinking,
            claude_effort=args.claude_effort,
            timeout=args.timeout,
            retries=args.retries,
            prompt=prompt,
            main_report_recorded=True,
        )

        emit_summary(
            run_dir,
            status,
            warnings=warnings,
            successful_reviewers=[item["reviewer"] for item in succeeded],
            failed_reviewers=[item["reviewer"] for item in failed],
            substitutions=[
                {"requested": requested_reviewer, "actual": actual}
                for requested_reviewer, actual in roster
                if requested_reviewer != actual
            ],
            main_agent_report=str(main_report_target),
            reports=results,
            default_models=default_reviewers,
            available_pi_models=available_pi_models,
            available_claude_models=available_claude_models,
            persisted_default_models=persisted_default_reviewers,
            default_models_config=str(config_path),
        )
        return 0 if status == "ready" else 3

    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        if run_dir is not None:
            error_path = run_dir / "input.md"
            if not error_path.exists():
                error_path.write_text(
                    "# Agent Council Input\n\n"
                    "The council aborted before reviewer calls completed.\n\n"
                    f"- Error: {exc}\n",
                    encoding="utf-8",
                )
        emit_summary(
            run_dir,
            "error",
            warnings=warnings,
            error=str(exc),
            default_models=default_reviewers,
            available_pi_models=available_pi_models,
            available_claude_models=available_claude_models,
            persisted_default_models=persisted_default_reviewers,
            default_models_config=str(config_path) if config_path else None,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
