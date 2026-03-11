"""xiaohongshu-scraper-codex 内部编排入口。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[2] / "xiaohongshu-core-codex" / "scripts"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from auth import XHSAuthSession
from schema import build_output_dir, mark_task_complete, write_execution_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="小红书 codex 编排器")
    parser.add_argument("--topic", help="搜索主旨；首次抓取时必填")
    parser.add_argument("--mode", choices=["fixed", "divergent"], default="fixed")
    parser.add_argument("--keywords", default="", help="固定模式关键词，逗号分隔")
    parser.add_argument("--max-posts", type=int, default=30)
    parser.add_argument("--hyperlinks", action="store_true")
    parser.add_argument("--output-root", default="data/xiaohongshu")
    parser.add_argument("--resume-dir", default="", help="复用已存在的输出目录，跳过登录与抓取，仅继续报告收尾")
    parser.add_argument("--draft", default="report_draft.md", help="报告草稿路径；相对路径默认相对于输出目录")
    parser.add_argument("--login-timeout", type=int, default=120)
    return parser.parse_args()


def build_fetch_command(output_dir: Path, args: argparse.Namespace) -> list[str]:
    fetch_script = Path(__file__).resolve().parents[2] / "xiaohongshu-fetch-codex" / "scripts" / "fetch_xhs.py"
    command = [
        sys.executable,
        str(fetch_script),
        "--keywords",
        args.keywords,
        "--max-posts",
        str(args.max_posts),
        "--output",
        str(output_dir / "raw.json"),
    ]
    if args.hyperlinks:
        command.append("--hyperlinks")
    return command


def build_report_command(output_dir: Path, draft_path: Path) -> list[str]:
    report_script = Path(__file__).resolve().parents[2] / "xiaohongshu-report-codex" / "scripts" / "build_report.py"
    return [sys.executable, str(report_script), "--dir", str(output_dir), "--draft", str(draft_path)]


def resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.resume_dir:
        return Path(args.resume_dir).resolve()
    if not args.topic:
        raise ValueError("首次执行必须提供 --topic，或通过 --resume-dir 继续已有目录")
    return build_output_dir(Path(args.output_root), args.topic)


def resolve_draft_path(output_dir: Path, draft_arg: str) -> Path:
    draft_path = Path(draft_arg)
    if draft_path.is_absolute():
        return draft_path
    return output_dir / draft_path


def print_report_handoff(output_dir: Path, draft_path: Path) -> None:
    report_script = Path(__file__).resolve().parents[2] / "xiaohongshu-report-codex" / "scripts" / "build_report.py"
    print(f"[orchestrator] RAW_JSON={output_dir / 'raw.json'}", flush=True)
    print(f"[orchestrator] REPORT_DRAFT_REQUIRED={draft_path}", flush=True)
    print(
        "[orchestrator] HANDOFF=请先让 LLM 按 xiaohongshu-report-codex/SKILL.md 读取 raw.json 生成完整 report_draft.md，"
        f"再执行: {sys.executable} {report_script} --dir {output_dir} --draft {draft_path}",
        flush=True,
    )


def ensure_tasks_file(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_file = output_dir / "tasks.md"
    if not tasks_file.exists():
        write_execution_tasks(tasks_file)
    return tasks_file


def main() -> int:
    args = parse_args()

    try:
        output_dir = resolve_output_dir(args)
    except ValueError as exc:
        print(f"[orchestrator] {exc}", flush=True)
        return 1

    tasks_file = ensure_tasks_file(output_dir)
    print(f"[orchestrator] OUTPUT_DIR={output_dir}", flush=True)

    if not args.resume_dir:
        auth = XHSAuthSession()
        login_state, _ = auth.ensure_login(timeout=args.login_timeout)
        print(f"[orchestrator] {login_state}", flush=True)
        if login_state not in {"LOGIN_OK", "LOGIN_SUCCESS"}:
            return 1
        mark_task_complete(tasks_file, "确保登录")

        fetch_command = build_fetch_command(output_dir, args)
        subprocess.run(fetch_command, check=True)
        mark_task_complete(tasks_file, "抓取数据")

    raw_path = output_dir / "raw.json"
    if not raw_path.exists():
        print(f"[orchestrator] 缺少 raw.json: {raw_path}", flush=True)
        return 1

    draft_path = resolve_draft_path(output_dir, args.draft)
    if not draft_path.exists():
        print_report_handoff(output_dir, draft_path)
        return 0

    report_command = build_report_command(output_dir, draft_path)
    subprocess.run(report_command, check=True)
    mark_task_complete(tasks_file, "生成报告")
    mark_task_complete(tasks_file, "发送报告")

    verify_script = Path(__file__).parent / "verify_tasks.py"
    subprocess.run([sys.executable, str(verify_script), str(tasks_file)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
