"""浏览器与平台相关共享能力（codex）。"""

from __future__ import annotations

import io
import os
import sys
from typing import Any


def configure_utf8_output() -> None:
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


configure_utf8_output()


def ensure_display() -> None:
    if sys.platform != "win32" and not os.environ.get("DISPLAY"):
        print("[✗] 检测到无 DISPLAY 环境变量", file=sys.stderr, flush=True)
        print("    请先启动虚拟显示器:", file=sys.stderr, flush=True)
        print("    Xvfb :99 -screen 0 1920x1080x24 &", file=sys.stderr, flush=True)
        print("    export DISPLAY=:99", file=sys.stderr, flush=True)
        sys.exit(1)


def build_launch_kwargs() -> dict[str, Any]:
    ensure_display()
    launch_kw: dict[str, Any] = {"headless": False}
    if sys.platform == "win32":
        launch_kw["channel"] = "msedge"
        launch_kw["args"] = ["--start-minimized"]
    return launch_kw
