"""验证小红书任务清单、raw.json 与最终报告。"""

import argparse
import hashlib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


EXPECTED_FIRST_SECTION = {
    "recommend": "选购结论",
    "plan": "方案结论",
    "factcheck": "结论与置信度",
    "explore": "议题地图",
}


def _normalize(value: str) -> str:
    return "".join(
        char for char in (value or "")
        if not char.isspace() and unicodedata.category(char) != "Cf"
    )


def _fingerprint(post: dict) -> str:
    payload = "".join((
        _normalize(post.get("author", "")),
        _normalize(post.get("title", "")),
        _normalize(post.get("content", ""))[:300],
    ))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _verify_tasks_file(path: Path, errors: list[str]) -> tuple[int, int]:
    if not path.exists():
        errors.append(f"TASKS_MISSING: {path}")
        return 0, 0
    content = path.read_text(encoding="utf-8")
    unchecked = re.findall(r"^- \[ \] (.+)$", content, re.MULTILINE)
    checked = re.findall(r"^- \[[xX]\] (.+)$", content, re.MULTILINE)
    if not checked and not unchecked:
        errors.append("TASKS_EMPTY: 未找到任务项")
    if unchecked:
        errors.append(f"TASKS_INCOMPLETE: {', '.join(item.strip() for item in unchecked)}")
    return len(checked), len(checked) + len(unchecked)


def _verify_raw(path: Path, errors: list[str]):
    if not path.exists():
        errors.append(f"RAW_MISSING: {path}")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"RAW_INVALID: {exc}")
        return

    posts = data.get("posts")
    dedup = data.get("dedup")
    if not isinstance(posts, list) or not posts:
        errors.append("RAW_POSTS_EMPTY: posts 必须是非空数组")
        return
    if not isinstance(dedup, dict):
        errors.append("RAW_DEDUP_MISSING: 缺少 dedup 统计块")
    else:
        if dedup.get("posts_unique") != len(posts):
            errors.append("RAW_DEDUP_COUNT: posts_unique 与 posts 实际长度不一致")
        if dedup.get("posts_scraped") != len(posts) + dedup.get("dropped_duplicate", 0):
            errors.append("RAW_DEDUP_TOTAL: posts_scraped 口径不一致")

    fingerprints = [_fingerprint(post) for post in posts]
    if len(fingerprints) != len(set(fingerprints)):
        errors.append("RAW_DUPLICATE: raw.json 仍含重复内容指纹")

    required = {"post_id", "url", "card_url", "title", "content", "author", "comments_count", "comments_captured", "comments"}
    for index, post in enumerate(posts):
        missing = sorted(required - post.keys())
        if missing:
            errors.append(f"RAW_POST_FIELDS[{index}]: 缺少 {', '.join(missing)}")
            continue
        if not post["post_id"] or post["post_id"] not in post["url"]:
            errors.append(f"RAW_POST_ID[{index}]: post_id 为空或与 url 不一致")
        comments = post["comments"]
        if not isinstance(comments, list):
            errors.append(f"RAW_COMMENTS[{index}]: comments 不是数组")
            continue
        if post["comments_captured"] != len(comments):
            errors.append(f"RAW_COMMENT_COUNT[{index}]: comments_captured 与实际长度不一致")
        for comment_index, comment in enumerate(comments):
            if not isinstance(comment, dict) or not {"text", "author", "likes", "is_reply"} <= comment.keys():
                errors.append(f"RAW_COMMENT_FIELDS[{index}:{comment_index}]: 评论未结构化")
                break


def _second_level_headings(content: str) -> list[str]:
    return [heading.strip() for heading in re.findall(r"^##\s+(.+?)\s*$", content, re.MULTILINE)]


def _verify_report(path: Path, report_type: str, hyperlinks: bool, errors: list[str]):
    if not path.exists():
        errors.append(f"REPORT_MISSING: {path}")
        return
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        errors.append("REPORT_EMPTY: 报告为空")
        return
    if "(id:" in content:
        errors.append("REPORT_ID_PLACEHOLDER: 存在未替换的 (id: 占位符")
    if hyperlinks and not (path.parent / "id_url_map.json").exists():
        errors.append("REPORT_LINK_MAP_MISSING: 超链接模式缺少 id_url_map.json")

    headings = _second_level_headings(content)
    if not any("搜索概览" in heading for heading in headings):
        errors.append("REPORT_OVERVIEW_MISSING: 缺少搜索概览")
        return
    scale_lines = [line for line in content.splitlines() if "数据规模" in line]
    if not scale_lines or not all(term in scale_lines[0] for term in ("独立内容", "实际分析", "来源页面累计")):
        errors.append("REPORT_SCALE: 数据规模缺少独立内容、实际分析评论或来源页面累计口径")
    decision_headings = [
        heading for heading in headings
        if not any(skip in heading for skip in ("搜索概览", "搜索发散路径", "数据来源说明"))
    ]
    expected = EXPECTED_FIRST_SECTION[report_type]
    if not decision_headings or expected not in decision_headings[0]:
        actual = decision_headings[0] if decision_headings else "<无>"
        errors.append(f"REPORT_ROUTE: {report_type} 首个决策板块应为 {expected}，实际为 {actual}")

    if report_type == "recommend":
        primary_rows = re.findall(r"^\|\s*首选\s*\|", content, re.MULTILINE)
        if len(primary_rows) != 1:
            errors.append(f"REPORT_PRIMARY: 首选行必须且只能有一行，实际 {len(primary_rows)} 行")


def verify_run(
    tasks_path: str,
    report_file: str,
    report_type: str,
    hyperlinks: bool = False,
) -> int:
    tasks = Path(tasks_path).resolve()
    report = Path(report_file).resolve()
    errors: list[str] = []
    if report.parent != tasks.parent:
        errors.append("REPORT_PATH: REPORT_FILE 必须位于 tasks.md 所在的 OUTPUT_DIR")
    completed, total = _verify_tasks_file(tasks, errors)
    _verify_raw(tasks.parent / "raw.json", errors)
    _verify_report(report, report_type, hyperlinks, errors)

    if errors:
        print(f"RUN_INVALID: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"TASKS_COMPLETE: {completed}/{total}")
    print(f"RUN_VALID: report_type={report_type}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="验证小红书运行产物")
    parser.add_argument("tasks_path")
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--report-type", required=True, choices=sorted(EXPECTED_FIRST_SECTION))
    parser.add_argument("--hyperlinks", action="store_true")
    args = parser.parse_args()
    sys.exit(verify_run(args.tasks_path, args.report_file, args.report_type, args.hyperlinks))


if __name__ == "__main__":
    main()
