"""
tasks.md 验证脚本

读取 tasks.md 文件，检查所有任务是否已完成。
用于 xiaohongshu-scraper 执行阶段结束前的强制验证。

用法：
    python verify_tasks.py <tasks_file_path>

输出：
    TASKS_COMPLETE: N/N        # 全部完成，返回 0
    TASKS_INCOMPLETE: N/N      # 有未完成项，返回 1
    未完成项：xxx, xxx          # 未完成项列表（如有）
"""

import io
import re
import sys
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def verify_tasks(tasks_path: str) -> int:
    """验证 tasks.md 是否全部完成"""
    path = Path(tasks_path)

    if not path.exists():
        print(f"ERROR: 文件不存在: {tasks_path}")
        return 1

    content = path.read_text(encoding="utf-8")

    # 匹配所有任务项：- [ ] 或 - [x]
    unchecked_pattern = r"- \[ \]"
    checked_pattern = r"- \[x\]"

    unchecked = re.findall(unchecked_pattern, content)
    checked = re.findall(checked_pattern, content)

    total = len(unchecked) + len(checked)
    completed = len(checked)

    if total == 0:
        print("ERROR: 未找到任何任务项")
        return 1

    if len(unchecked) == 0:
        print(f"TASKS_COMPLETE: {completed}/{total}")
        return 0
    else:
        print(f"TASKS_INCOMPLETE: {completed}/{total}")

        # 提取未完成项的描述
        lines = content.split("\n")
        unchecked_items = []
        for line in lines:
            if re.match(r"- \[ \]", line):
                # 提取任务描述（去掉 "- [ ] " 前缀）
                desc = re.sub(r"- \[ \] ", "", line).strip()
                if desc:
                    unchecked_items.append(desc)

        if unchecked_items:
            print(f"未完成项：{', '.join(unchecked_items)}")

        return 1


def main():
    if len(sys.argv) < 2:
        print("用法: python verify_tasks.py <tasks_file_path>")
        sys.exit(1)

    exit_code = verify_tasks(sys.argv[1])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
