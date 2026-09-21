#!/usr/bin/env python3
"""查看与清理任务工作区产物；清理默认预览，仅 --apply 执行。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

TASK_ID = re.compile(r"[0-9]{8}_[0-9]{6}_[a-z0-9]+(-[a-z0-9]+){1,4}")
WORK_PARTS = {"scratch", "runner"}
LEGACY_DIRS = (".tmp", ".prototypes", ".prototype", ".task-runner", ".scratch", "plans", "docs/plans")


def repo_root(start: Path) -> Path:
    out = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(out.stdout.strip()).resolve() if out.returncode == 0 else start.resolve()


def candidates(root: Path):
    for name in (".work", ".local"):
        base = root / name
        if base.is_dir():
            yield from sorted(p for p in base.iterdir() if p.is_dir())
    for name in LEGACY_DIRS:
        if (root / name).exists():
            yield root / name


def members(path: Path):
    yield path
    if path.is_dir() and not path.is_symlink():
        for base, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                yield Path(base) / name


def active_users(path: Path) -> list[int] | None:
    """同一用户进程的 cwd、打开文件与命令参数引用；无 /proc 时返回 None。"""
    proc = Path("/proc")
    if not proc.is_dir():
        return None
    found = set()
    for item in proc.iterdir():
        if not item.name.isdigit() or int(item.name) in (os.getpid(), os.getppid()):
            continue
        try:
            if item.stat().st_uid != os.getuid():
                continue
            refs = [os.readlink(item / "cwd")]
            refs += (item / "cmdline").read_bytes().decode(errors="replace").split("\0")
            for fd in (item / "fd").iterdir():
                try:
                    refs.append(os.readlink(fd))
                except OSError:
                    pass
            if any(ref == str(path) or ref.startswith(str(path) + "/") for ref in refs):
                found.add(int(item.name))
        except (OSError, ProcessLookupError):
            continue
    return sorted(found)


def validate(root: Path, value: str) -> Path:
    path = Path(os.path.abspath(root / value))
    try:
        rel = path.relative_to(root)
    except ValueError:
        raise ValueError("目标必须位于工作区内") from None
    allowed = (rel.parts[:1] == (".work",) and len(rel.parts) in (2, 3)
               and TASK_ID.fullmatch(rel.parts[1]) is not None
               and (len(rel.parts) == 2 or rel.name in WORK_PARTS))
    if not allowed:
        raise ValueError("仅接受任务 ID 合规的 .work/<任务ID> 及其 scratch、runner")
    if not path.is_dir() or path.resolve() != path:
        raise ValueError("目标必须是存在的真实目录，路径不能经过符号链接")
    if any(p.is_symlink() for p in members(path)):
        raise ValueError("目录含符号链接，请单独审核处理")
    tracked = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--", rel.as_posix()], capture_output=True).stdout
    if tracked:
        raise ValueError("目标包含 Git 跟踪文件")
    busy = active_users(path)
    if busy:
        raise ValueError(f"目标正被进程使用：{busy}")
    return path


def describe(root: Path, path: Path, action: str) -> dict:
    rel = path.relative_to(root)
    row = {"path": rel.as_posix(), "bytes": sum(p.lstat().st_size for p in members(path) if not p.is_dir())}
    if rel.parts[0] == ".work" and len(rel.parts) == 2:
        row["task_id_ok"] = TASK_ID.fullmatch(rel.name) is not None
    elif rel.as_posix() in LEGACY_DIRS:
        row["legacy"] = True
    row["active_pids"] = active_users(path)
    row["action"] = action
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "clean"])
    parser.add_argument("paths", nargs="*", help="已结束任务的具体目录，相对工作区根")
    parser.add_argument("--root", help="工作区根，默认取当前目录所在 Git 仓库根")
    parser.add_argument("--apply", action="store_true", help="执行列出的清理；默认只预览")
    args = parser.parse_args()
    root = Path(args.root).resolve() if args.root else repo_root(Path.cwd())
    if args.action == "list":
        if args.paths or args.apply:
            parser.error("list 不接受目标路径或 --apply")
        paths = list(candidates(root))
    else:
        if not args.paths:
            parser.error("clean 必须明确列出目标目录")
        try:
            paths = [validate(root, value) for value in args.paths]
        except ValueError as exc:
            parser.error(str(exc))
    for path in paths:
        print(json.dumps(describe(root, path, "delete" if args.apply else "inspect"), ensure_ascii=False))
    if args.apply:
        for path in paths:
            validate(root, str(path.relative_to(root)))
            shutil.rmtree(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
