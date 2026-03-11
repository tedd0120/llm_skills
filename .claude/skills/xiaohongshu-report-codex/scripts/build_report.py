"""统一报告流水线（codex finalizer）。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[2] / "xiaohongshu-core-codex" / "scripts"
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from schema import mark_task_complete

TOOL_VERSION = "xiaohongshu-scraper-codex v1.0"
DISCLAIMER = (
    "本报告由 AI 自动生成，数据来源于小红书平台用户评论。报告中所有品牌/店铺推荐、避雷评价、"
    "价格信息均来自用户真实反馈，AI 仅负责归纳整理。内容仅供参考，不构成任何消费建议。"
    "对于因使用本报告内容造成的任何损失，AI 不承担责任。"
)
TITLE_TEMPLATE = "# 🔎 {topic} 报告 🔎"
SECTION_HEADINGS = {
    "搜索概览": "## 📊 搜索概览",
    "搜索发散路径": "## 🧭 搜索发散路径",
    "品牌/主题声量分析": "## 🔥 品牌/主题声量分析",
    "评论区高频共识": "## 💬 评论区高频共识",
    "场景化决策建议": "## 🎯 场景化决策建议",
    "价格/规格参考": "## 💰 价格/规格参考",
    "避雷指南": "## ⚠️ 避雷指南",
    "关键洞察": "## 🔍 关键洞察",
    "数据来源说明": "## 📍 数据来源说明",
}
SUBSECTION_HEADINGS = {
    "核心优点": "### ✨ 核心优点 (Top 5)",
    "核心痛点": "### 😤 核心痛点 (Top 5)",
}
MAJOR_SECTION_LINES = {heading for key, heading in SECTION_HEADINGS.items() if key != "数据来源说明"}
PLACEHOLDER_LINK_RE = re.compile(r"\[([^\n\]]+?)\]\(id:([^\)]+)\)")
PLACEHOLDER_URL_RE = re.compile(r"\(id:([^\)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="小红书 codex 报告 finalizer")
    parser.add_argument("--dir", required=True, help="包含 raw.json 的输出目录")
    parser.add_argument("--draft", default="report_draft.md", help="草稿文件路径，默认读取输出目录下的 report_draft.md")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_topic(output_dir: Path) -> str:
    name = output_dir.name
    parts = name.split("_", 2)
    if len(parts) == 3:
        return parts[2].replace("_", " ")
    return name.replace("_", " ")


def format_time(search_time: str) -> str:
    return (search_time or "")[:16]


def build_reference_url(post: dict, id_url_map: dict[str, str]) -> str | None:
    post_id = (post.get("post_id") or "").strip()
    if not post_id:
        return None
    if post_id in id_url_map:
        return f"https://www.xiaohongshu.com/explore/{post_id}"
    if id_url_map:
        return f"https://www.xiaohongshu.com/explore/{post_id}"
    return None


def resolve_draft_path(output_dir: Path, draft_arg: str) -> Path:
    draft_path = Path(draft_arg)
    if draft_path.is_absolute():
        return draft_path
    return output_dir / draft_path


def require_text_file(path: Path, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"缺少 {label}: {path}")
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"{label} 为空: {path}")
    return content


def validate_draft(draft_text: str, draft_path: Path) -> None:
    if "搜索概览" not in draft_text:
        raise ValueError(f"草稿格式不合法，缺少“搜索概览”章节: {draft_path}")


def build_post_lookup(raw: dict) -> dict[str, dict]:
    posts = raw.get("posts") or []
    return {str(post.get("post_id") or "").strip(): post for post in posts if str(post.get("post_id") or "").strip()}


def resolve_reference_url(post_id: str, posts_by_id: dict[str, dict], id_url_map: dict[str, str]) -> str | None:
    post_id = post_id.strip()
    post = posts_by_id.get(post_id, {"post_id": post_id})
    return build_reference_url(post, id_url_map)


def render_reference_links(text: str, posts_by_id: dict[str, dict], id_url_map: dict[str, str]) -> str:
    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        post_id = match.group(2)
        url = resolve_reference_url(post_id, posts_by_id, id_url_map)
        if url:
            return f"[{label}]({url})"
        return label

    def replace_url(match: re.Match[str]) -> str:
        post_id = match.group(1)
        url = resolve_reference_url(post_id, posts_by_id, id_url_map)
        if url:
            return f"({url})"
        return ""

    text = PLACEHOLDER_LINK_RE.sub(replace_link, text)
    return PLACEHOLDER_URL_RE.sub(replace_url, text)


def cleanup_comment_prefixes(text: str) -> str:
    text = text.replace('_":"', '_"')
    text = re.sub(r'_(?:"|“)\s*:\s*(?:"|“)', '_"', text)
    return text


def strip_data_source_section(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    for line in lines:
        match = HEADING_RE.match(line.strip())
        if match and match.group(1) == "##" and "数据来源说明" in match.group(2):
            break
        kept.append(line.rstrip())
    return "\n".join(kept).strip()


def normalize_heading_line(line: str, topic: str) -> str:
    stripped = line.strip()
    match = HEADING_RE.match(stripped)
    if not match:
        return line.rstrip()

    level, heading_text = match.groups()
    if level == "#":
        return TITLE_TEMPLATE.format(topic=topic)
    if level == "##":
        for keyword, heading in SECTION_HEADINGS.items():
            if keyword in heading_text:
                return heading
    if level == "###":
        for keyword, heading in SUBSECTION_HEADINGS.items():
            if keyword in heading_text:
                return heading
    return stripped


def ensure_title(text: str, topic: str) -> str:
    lines = text.splitlines()
    title_line = TITLE_TEMPLATE.format(topic=topic)
    for index, line in enumerate(lines):
        if line.strip().startswith("# "):
            lines[index] = title_line
            return "\n".join(lines)
    return "\n".join([title_line, "", *lines]).strip()


def normalize_headings(text: str, topic: str) -> str:
    lines = [normalize_heading_line(line, topic) for line in text.splitlines()]
    return "\n".join(lines)


def ensure_major_section_dividers(text: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    seen_first_major = False

    for line in lines:
        stripped = line.strip()
        if stripped in MAJOR_SECTION_LINES:
            while output and output[-1] == "":
                output.pop()
            if seen_first_major:
                if output and output[-1] != "---":
                    output.extend(["", "---", ""])
            elif output and output[-1] != "":
                output.append("")
            seen_first_major = True
            output.append(stripped)
            continue
        output.append(line.rstrip())

    return "\n".join(output).strip()


def build_data_source_section(raw: dict) -> str:
    return "\n".join(
        [
            SECTION_HEADINGS["数据来源说明"],
            "",
            f"> {DISCLAIMER}",
            "",
            f"- 报告生成时间：{format_time(raw.get('search_time', ''))}",
            f"- 工具版本：{TOOL_VERSION}",
        ]
    )


def finalize_report(draft_text: str, raw: dict, output_dir: Path, id_url_map: dict[str, str]) -> str:
    topic = infer_topic(output_dir)
    posts_by_id = build_post_lookup(raw)
    text = strip_data_source_section(draft_text)
    text = normalize_headings(text, topic)
    text = ensure_title(text, topic)
    text = render_reference_links(text, posts_by_id, id_url_map)
    text = cleanup_comment_prefixes(text)
    text = ensure_major_section_dividers(text)
    text = f"{text}\n\n---\n\n{build_data_source_section(raw)}"
    return text.strip() + "\n"


def mark_report_task_complete(output_dir: Path) -> None:
    tasks_file = output_dir / "tasks.md"
    if tasks_file.exists():
        mark_task_complete(tasks_file, "生成报告")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.dir).resolve()
    draft_path = resolve_draft_path(output_dir, args.draft)

    try:
        raw = load_json(output_dir / "raw.json")
        draft_text = require_text_file(draft_path, "report_draft.md")
        validate_draft(draft_text, draft_path)
        id_url_map_path = output_dir / "id_url_map.json"
        id_url_map = load_json(id_url_map_path) if id_url_map_path.exists() else {}
        report = finalize_report(draft_text, raw, output_dir, id_url_map)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"[x] {exc}", file=sys.stderr, flush=True)
        return 1

    report_path = output_dir / "_index.md"
    report_path.write_text(report, encoding="utf-8")
    mark_report_task_complete(output_dir)
    print(f"[✓] 报告已定稿 → {report_path}", flush=True)
    print(f"[✓] 使用草稿文件 → {draft_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
