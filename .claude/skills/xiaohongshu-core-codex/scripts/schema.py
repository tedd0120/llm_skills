"""共享数据与任务文件辅助（codex）。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

INVALID_CHAR_TRANSLATIONS = str.maketrans(
    {
        "\\": "＼",
        "/": "／",
        ":": "：",
        "*": "＊",
        "?": "？",
        '"': "＂",
        "<": "＜",
        ">": "＞",
        "|": "｜",
    }
)
MAX_TOPIC_SEGMENT_LENGTH = 80
OUTPUT_DIR_TOPIC_RE = re.compile(r"^\d{8}_\d{6}_(.+)$")


def slugify_topic(topic: str) -> str:
    cleaned = re.sub(r"[\x00-\x1f]", "", topic.strip())
    cleaned = cleaned.translate(INVALID_CHAR_TRANSLATIONS)
    cleaned = re.sub(r"\s+", " ", cleaned).rstrip(" .")
    if len(cleaned) > MAX_TOPIC_SEGMENT_LENGTH:
        cleaned = cleaned[:MAX_TOPIC_SEGMENT_LENGTH].rstrip(" .")
    return cleaned or "xiaohongshu"


def infer_topic_from_output_dir(output_dir: Path) -> str:
    match = OUTPUT_DIR_TOPIC_RE.match(output_dir.name)
    if match:
        return match.group(1)
    return output_dir.name.replace("_", " ")


def allocate_quotas(total: int, buckets: int) -> list[int]:
    if buckets <= 0:
        return []
    base = total // buckets
    remainder = total % buckets
    return [base + (1 if index < remainder else 0) for index in range(buckets)]


def normalize_keywords(raw_keywords: str) -> list[str]:
    return [keyword.strip() for keyword in raw_keywords.split(",") if keyword.strip()]


def resolve_draft_path(output_dir: Path, draft_arg: str) -> Path:
    draft_path = Path(draft_arg)
    if draft_path.is_absolute():
        return draft_path
    return output_dir / draft_path


def require_text_file(path: Path, label: str) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"缺少 {label}: {path}") from exc
    if not content.strip():
        raise ValueError(f"{label} 为空: {path}")
    return content


def build_explore_url(post_id: str) -> str:
    return f"https://www.xiaohongshu.com/explore/{post_id}"


def build_post_id_url_map(posts: list[dict]) -> dict[str, str]:
    id_url_map: dict[str, str] = {}
    for post in posts:
        post_id = str(post.get("post_id") or "").strip()
        if post_id:
            id_url_map[post_id] = build_explore_url(post_id)
    return id_url_map


def build_post_lookup(posts: list[dict]) -> dict[str, dict]:
    return {str(post.get("post_id") or "").strip(): post for post in posts if str(post.get("post_id") or "").strip()}


def build_output_dir(base_dir: Path, topic: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_dir / f"{timestamp}_{slugify_topic(topic)}"


def write_execution_tasks(tasks_file: Path) -> None:
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        "## 执行任务清单\n\n"
        "- [ ] 确保登录\n"
        "- [ ] 抓取数据\n"
        "- [ ] 生成报告\n"
        "- [ ] 发送报告\n",
        encoding="utf-8",
    )


def mark_task_complete(tasks_file: Path, task_name: str) -> bool:
    content = tasks_file.read_text(encoding="utf-8")
    checked_item = f"- [x] {task_name}"
    unchecked_item = f"- [ ] {task_name}"
    if checked_item in content or unchecked_item not in content:
        return False
    tasks_file.write_text(content.replace(unchecked_item, checked_item), encoding="utf-8")
    return True


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
