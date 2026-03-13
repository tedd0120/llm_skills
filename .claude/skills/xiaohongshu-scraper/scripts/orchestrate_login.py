"""
小红书登录编排脚本
负责启动 login_xhs.py、轮询增量输出、转发结构化登录事件，并可选更新 tasks.md。
"""

import argparse
import io
import json
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent.resolve()
LOGIN_SCRIPT = (SCRIPT_DIR / "login_xhs.py").resolve()
DEFAULT_POLL_INTERVAL_SEC = 2.0
SUCCESS_MARKERS = {"LOGIN_OK", "LOGIN_SUCCESS"}
FAILURE_MARKERS = {"LOGIN_TIMEOUT", "LOGIN_FAILED"}


def emit_event(event: str, **payload) -> None:
    body = {"event": event, **payload}
    print(f"LOGIN_EVENT: {json.dumps(body, ensure_ascii=False)}", flush=True)


def normalize_poll_interval(raw_value: str) -> float:
    reason = None
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        value = DEFAULT_POLL_INTERVAL_SEC
        reason = f"非数字: {raw_value!r}"
    else:
        if value <= 0:
            value = DEFAULT_POLL_INTERVAL_SEC
            reason = f"<= 0: {raw_value!r}"
        elif value < 1 or value > 10:
            value = DEFAULT_POLL_INTERVAL_SEC
            reason = f"超出建议范围 1-10: {raw_value!r}"

    if reason:
        print(
            f"LOGIN_POLL_INTERVAL_SEC_INVALID: {reason}; 回退到默认值 {int(DEFAULT_POLL_INTERVAL_SEC)}",
            flush=True,
        )
    return value


def update_login_task(tasks_file: Path) -> None:
    if not tasks_file.exists():
        raise FileNotFoundError(f"tasks.md 文件不存在: {tasks_file}")

    content = tasks_file.read_text(encoding="utf-8")
    checked_line = "- [x] 确保登录"
    unchecked_pattern = r"- \[ \] 确保登录"

    if checked_line in content:
        return

    updated, count = re.subn(unchecked_pattern, checked_line, content, count=1)
    if count != 1:
        raise ValueError(f"未找到可更新的任务项: {tasks_file}")

    tasks_file.write_text(updated, encoding="utf-8")


def enqueue_output(stream, output_queue: queue.Queue) -> None:
    try:
        for line in iter(stream.readline, ""):
            output_queue.put(line)
    finally:
        stream.close()
        output_queue.put(None)


def run_login(timeout: int, poll_interval: float, tasks_file: Path | None) -> int:
    command = [sys.executable, str(LOGIN_SCRIPT), "--timeout", str(timeout)]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(SCRIPT_DIR),
    )

    emit_event(
        "STARTED",
        script=str(LOGIN_SCRIPT),
        pid=process.pid,
        timeout=timeout,
        poll_interval=poll_interval,
        tasks_file=str(tasks_file.resolve()) if tasks_file else None,
    )

    assert process.stdout is not None
    output_queue: queue.Queue = queue.Queue()
    reader = threading.Thread(target=enqueue_output, args=(process.stdout, output_queue), daemon=True)
    reader.start()

    seen_need_login = False
    terminal_marker = None
    stream_closed = False

    while True:
        drained = False
        while True:
            try:
                item = output_queue.get_nowait()
            except queue.Empty:
                break

            drained = True
            if item is None:
                stream_closed = True
                break

            line = item.rstrip("\r\n")
            print(line, flush=True)

            if line.startswith("NEED_LOGIN:"):
                qr_path = line.split(":", 1)[1]
                if not seen_need_login:
                    emit_event("NEED_LOGIN", path=qr_path)
                    seen_need_login = True
            elif line in SUCCESS_MARKERS:
                terminal_marker = line
                emit_event(line)
            elif line in FAILURE_MARKERS:
                terminal_marker = line
                emit_event(line)

        if terminal_marker in SUCCESS_MARKERS:
            if tasks_file:
                update_login_task(tasks_file)
                emit_event("TASK_UPDATED", tasks_file=str(tasks_file.resolve()), task="确保登录", status="completed")
            process.wait()
            emit_event("EXIT", code=0, result=terminal_marker)
            return 0

        if terminal_marker in FAILURE_MARKERS:
            process.wait()
            emit_event("EXIT", code=process.returncode or 1, result=terminal_marker)
            return process.returncode or 1

        if stream_closed and process.poll() is not None:
            break

        if not drained:
            time.sleep(poll_interval)

    return_code = process.wait()
    if return_code == 0:
        emit_event("LOGIN_SUCCESS", inferred=True)
        if tasks_file:
            update_login_task(tasks_file)
            emit_event("TASK_UPDATED", tasks_file=str(tasks_file.resolve()), task="确保登录", status="completed")
        emit_event("EXIT", code=0, result="LOGIN_SUCCESS")
        return 0

    emit_event("LOGIN_FAILED", inferred=True, returncode=return_code)
    emit_event("EXIT", code=return_code, result="LOGIN_FAILED")
    return return_code


def main() -> None:
    parser = argparse.ArgumentParser(description="小红书登录编排工具")
    parser.add_argument("--timeout", type=int, default=120, help="扫码等待超时秒数，默认 120")
    parser.add_argument(
        "--poll-interval",
        default=str(int(DEFAULT_POLL_INTERVAL_SEC)),
        help="登录输出轮询间隔（秒），默认 2；非法值回退到 2",
    )
    parser.add_argument("--tasks-file", help="可选，登录成功后自动勾选 tasks.md 中的“确保登录”")
    args = parser.parse_args()

    poll_interval = normalize_poll_interval(args.poll_interval)
    tasks_file = Path(args.tasks_file).resolve() if args.tasks_file else None

    try:
        code = run_login(timeout=args.timeout, poll_interval=poll_interval, tasks_file=tasks_file)
    except Exception as exc:
        emit_event("ORCHESTRATOR_ERROR", message=str(exc))
        print(f"ORCHESTRATOR_ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)

    sys.exit(code)


if __name__ == "__main__":
    main()
