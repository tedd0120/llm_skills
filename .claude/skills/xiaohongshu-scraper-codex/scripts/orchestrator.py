"""xiaohongshu-scraper-codex 内部编排入口。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[2] / "xiaohongshu-core-codex" / "scripts"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from auth import XHSAuthSession
from schema import allocate_quotas, build_output_dir, mark_task_complete, normalize_keywords, read_json, resolve_draft_path, write_execution_tasks, write_json

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "xiaohongshu"
MAX_POSTS_LIMIT = 100
MIN_DIVERGENT_ROUNDS = 1
MAX_DIVERGENT_ROUNDS = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="小红书 codex 编排器")
    parser.add_argument("--topic", help="搜索主旨；首次抓取时必填")
    parser.add_argument("--mode", choices=["fixed", "divergent"], default="fixed")
    parser.add_argument("--keywords", default="", help="固定模式关键词，逗号分隔；发散模式默认取首个关键词作为起始词")
    parser.add_argument("--max-posts", type=int, default=30)
    parser.add_argument("--rounds", type=int, default=3, help="发散模式轮数；fixed 模式忽略")
    parser.add_argument("--hyperlinks", action="store_true")
    parser.add_argument("--output-root", default="", help="已弃用；输出始终固定到仓库根目录 data/xiaohongshu")
    parser.add_argument("--resume-dir", default="", help="复用已存在的输出目录，跳过登录与抓取，仅继续报告收尾")
    parser.add_argument("--draft", default="report_draft.md", help="报告草稿路径；相对路径默认相对于输出目录")
    parser.add_argument("--login-timeout", type=int, default=120)
    return parser.parse_args()


def enforce_run_constraints(args: argparse.Namespace) -> None:
    if args.output_root:
        print(
            f"[orchestrator] 忽略 --output-root={args.output_root}；输出目录固定为 {DEFAULT_OUTPUT_ROOT}",
            flush=True,
        )
    if args.max_posts < 1 or args.max_posts > MAX_POSTS_LIMIT:
        raise ValueError(f"--max-posts 必须在 1-{MAX_POSTS_LIMIT} 之间")
    if args.mode == "fixed":
        if args.rounds < MIN_DIVERGENT_ROUNDS:
            raise ValueError("--rounds 必须为正整数")
        return
    if args.rounds < MIN_DIVERGENT_ROUNDS or args.rounds > MAX_DIVERGENT_ROUNDS:
        raise ValueError(f"发散模式 --rounds 必须在 {MIN_DIVERGENT_ROUNDS}-{MAX_DIVERGENT_ROUNDS} 之间")


def ensure_within_output_root(path: Path, label: str, must_exist: bool = False) -> Path:
    resolved = path.resolve()
    output_root = DEFAULT_OUTPUT_ROOT.resolve()
    try:
        resolved.relative_to(output_root)
    except ValueError as exc:
        raise ValueError(f"{label} 必须位于 {output_root} 下: {resolved}") from exc
    if must_exist and not resolved.exists():
        raise ValueError(f"{label} 不存在: {resolved}")
    return resolved


def build_divergent_plan(topic: str, seed_keywords: list[str], max_posts: int, rounds: int) -> list[dict]:
    quotas = allocate_quotas(max_posts, rounds)
    base_topic = topic.strip()
    plan: list[dict] = []
    seen_keywords: set[str] = set()

    def pick_keyword(candidates: list[str], fallback_index: int) -> str:
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in seen_keywords:
                seen_keywords.add(normalized)
                return normalized
        fallback = f"{base_topic} 第{fallback_index}轮"
        seen_keywords.add(fallback)
        return fallback

    for index, quota in enumerate(quotas, start=1):
        if index == 1:
            keyword = pick_keyword(seed_keywords or [base_topic], index)
            reason = "首轮围绕主题建立基础样本"
        else:
            keyword = pick_keyword(
                [
                    f"{base_topic} 经验",
                    f"{base_topic} 对比",
                    f"{base_topic} 避坑",
                    f"{base_topic} 推荐",
                    f"{base_topic} 评测",
                ],
                index,
            )
            reason = f"第 {index} 轮延展到新的相关搜索角度"
        plan.append(
            {
                "round": index,
                "keyword": keyword,
                "quota": quota,
                "reason": reason,
            }
        )
    return plan


def build_fetch_command(
    output_file: Path,
    keywords: list[str],
    max_posts: int,
    search_strategy: list[dict],
    seen_ids_path: Path | None,
    hyperlinks: bool,
) -> list[str]:
    fetch_script = Path(__file__).resolve().parents[2] / "xiaohongshu-fetch-codex" / "scripts" / "fetch_xhs.py"
    command = [
        sys.executable,
        str(fetch_script),
        "--keywords",
        ",".join(keywords),
        "--max-posts",
        str(max_posts),
        "--output",
        str(output_file),
        "--search-strategy",
        json.dumps(search_strategy, ensure_ascii=False),
    ]
    if seen_ids_path is not None:
        command.extend(["--seen-ids", str(seen_ids_path)])
    if hyperlinks:
        command.append("--hyperlinks")
    return command


def build_report_command(output_dir: Path, draft_path: Path) -> list[str]:
    report_script = Path(__file__).resolve().parents[2] / "xiaohongshu-report-codex" / "scripts" / "build_report.py"
    return [sys.executable, str(report_script), "--dir", str(output_dir), "--draft", str(draft_path)]


def resolve_output_dir(args: argparse.Namespace) -> Path:
    if args.resume_dir:
        return ensure_within_output_root(Path(args.resume_dir), "--resume-dir", must_exist=True)
    if not args.topic:
        raise ValueError("首次执行必须提供 --topic，或通过 --resume-dir 继续已有目录")
    return build_output_dir(DEFAULT_OUTPUT_ROOT, args.topic)


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


def merge_round_outputs(output_dir: Path, topic: str, rounds_plan: list[dict]) -> None:
    posts: list[dict] = []
    combined_keywords: list[str] = []
    divergence_path: list[dict] = []

    for round_spec in rounds_plan:
        round_file = output_dir / f"raw_round_{round_spec['round']}.json"
        round_data = read_json(round_file)
        round_posts = round_data.get("posts") or []
        posts.extend(round_posts)
        for keyword in round_data.get("keywords") or []:
            if keyword not in combined_keywords:
                combined_keywords.append(keyword)
        divergence_path.append(
            {
                "round": round_spec["round"],
                "keyword": round_spec["keyword"],
                "planned_posts": round_spec["quota"],
                "actual_posts": len(round_posts),
                "reason": round_spec["reason"],
                "raw_file": round_file.name,
            }
        )

    payload = {
        "search_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "mode": "divergent",
        "rounds": len(rounds_plan),
        "round_quotas": [round_spec["quota"] for round_spec in rounds_plan],
        "keywords": combined_keywords,
        "search_strategy": [
            {
                "keyword": round_spec["keyword"],
                "posts_count": round_spec["quota"],
                "intent": round_spec["reason"],
                "round": round_spec["round"],
            }
            for round_spec in rounds_plan
        ],
        "divergence_path": divergence_path,
        "posts": posts,
    }
    write_json(output_dir / "raw.json", payload)
    write_json(
        output_dir / "rounds.json",
        {
            "topic": topic,
            "mode": "divergent",
            "rounds": divergence_path,
        },
    )


def build_fixed_search_strategy(keywords: list[str], max_posts: int) -> list[dict]:
    return [
        {
            "keyword": keyword,
            "posts_count": quota,
            "intent": "固定模式抓取",
        }
        for keyword, quota in zip(keywords, allocate_quotas(max_posts, len(keywords)), strict=False)
    ]


def run_fixed_fetch(output_dir: Path, args: argparse.Namespace) -> None:
    keywords = normalize_keywords(args.keywords)
    if not keywords:
        if not args.topic:
            raise ValueError("fixed 模式必须提供 --keywords，或至少提供 --topic 作为默认关键词")
        keywords = [args.topic.strip()]
    command = build_fetch_command(
        output_file=output_dir / "raw.json",
        keywords=keywords,
        max_posts=args.max_posts,
        search_strategy=build_fixed_search_strategy(keywords, args.max_posts),
        seen_ids_path=None,
        hyperlinks=args.hyperlinks,
    )
    subprocess.run(command, check=True)


def run_divergent_fetch(output_dir: Path, args: argparse.Namespace) -> None:
    if not args.topic:
        raise ValueError("divergent 模式必须提供 --topic")
    seed_keywords = normalize_keywords(args.keywords)
    rounds_plan = build_divergent_plan(args.topic, seed_keywords, args.max_posts, args.rounds)
    seen_ids_path = output_dir / "seen_ids.txt"
    for round_spec in rounds_plan:
        round_output = output_dir / f"raw_round_{round_spec['round']}.json"
        print(
            f"[orchestrator] ROUND {round_spec['round']}/{len(rounds_plan)} KEYWORD={round_spec['keyword']} QUOTA={round_spec['quota']}",
            flush=True,
        )
        command = build_fetch_command(
            output_file=round_output,
            keywords=[round_spec["keyword"]],
            max_posts=round_spec["quota"],
            search_strategy=[
                {
                    "keyword": round_spec["keyword"],
                    "posts_count": round_spec["quota"],
                    "intent": round_spec["reason"],
                    "round": round_spec["round"],
                }
            ],
            seen_ids_path=seen_ids_path,
            hyperlinks=args.hyperlinks,
        )
        subprocess.run(command, check=True)
    merge_round_outputs(output_dir, args.topic, rounds_plan)


def run_fetch(output_dir: Path, args: argparse.Namespace) -> None:
    if args.mode == "divergent":
        run_divergent_fetch(output_dir, args)
        return
    run_fixed_fetch(output_dir, args)


def main() -> int:
    args = parse_args()

    try:
        enforce_run_constraints(args)
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

        try:
            run_fetch(output_dir, args)
        except ValueError as exc:
            print(f"[orchestrator] {exc}", flush=True)
            return 1
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
    mark_task_complete(tasks_file, "发送报告")

    verify_script = Path(__file__).parent / "verify_tasks.py"
    subprocess.run([sys.executable, str(verify_script), str(tasks_file)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
