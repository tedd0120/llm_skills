"""codex 执行阶段任务校验。"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def verify_tasks(tasks_path: str) -> int:
    path = Path(tasks_path)
    if not path.exists():
        print(f"ERROR: 文件不存在: {tasks_path}")
        return 1

    content = path.read_text(encoding="utf-8")
    unchecked = re.findall(r"- \[ \]", content)
    checked = re.findall(r"- \[x\]", content)
    total = len(unchecked) + len(checked)
    completed = len(checked)

    if total == 0:
        print("ERROR: 未找到任何任务项")
        return 1

    if not unchecked:
        print(f"TASKS_COMPLETE: {completed}/{total}")
        return 0

    print(f"TASKS_INCOMPLETE: {completed}/{total}")
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python verify_tasks.py <tasks_file_path>")
        sys.exit(1)
    sys.exit(verify_tasks(sys.argv[1]))
