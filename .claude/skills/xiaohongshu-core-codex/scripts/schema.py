"""共享数据与任务文件辅助（codex）。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


def slugify_topic(topic: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", topic.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:50] or "xiaohongshu"


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


def mark_task_complete(tasks_file: Path, task_name: str) -> None:
    content = tasks_file.read_text(encoding="utf-8")
    updated = content.replace(f"- [ ] {task_name}", f"- [x] {task_name}")
    tasks_file.write_text(updated, encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
