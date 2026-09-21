#!/usr/bin/env python3
"""只读盘点工作区目录：分类猜测、Git 跟踪与忽略状态、代码引用、进程占用和待确认项。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import json
import os
from pathlib import Path
import subprocess
import sys

KNOWN = Path(__file__).resolve().parents[1] / "references" / "known-paths.json"
MAX_DEPTH = 4
MAX_FILES = 100_000
MAX_REFS = 5
TEMPLATE_SUFFIXES = (".example", ".sample", ".template")


def git(root: Path, *args: str, stdin: bytes | None = None) -> bytes | None:
    try:
        return subprocess.run(["git", "-C", str(root), *args], input=stdin, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def split0(raw: bytes | None) -> list[str]:
    return [p for p in (raw or b"").decode("utf-8", "replace").split("\0") if p]


def load_known() -> list[dict]:
    return json.loads(KNOWN.read_text(encoding="utf-8"))["entries"]


def classify(rel: str, known: list[dict]) -> dict | None:
    name = rel.rsplit("/", 1)[-1]
    if name.startswith(".env") and name.endswith(TEMPLATE_SUFFIXES):
        return {"match": name, "layer": "asset", "ignore": "no", "note": "配置模板"}
    for entry in known:
        pattern = entry["match"]
        if pattern.startswith("/"):
            hit = fnmatch.fnmatchcase(rel, pattern[1:])
        else:
            hit = fnmatch.fnmatchcase(name, pattern) and (not entry.get("top_only") or "/" not in rel)
        if hit:
            return entry
    return None


def walk_candidates(root: Path, known: list[dict]):
    """根层级全部条目，以及深层中命中非 asset 分类的目录。"""
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        rel = child.name
        entry = classify(rel, known)
        if entry and entry.get("skip"):
            continue
        yield child, rel, entry
        if child.is_dir() and not child.is_symlink() and (entry is None or entry["layer"] == "asset"):
            yield from walk_nested(root, child, known, 2)


def walk_nested(root: Path, base: Path, known: list[dict], depth: int):
    if depth > MAX_DEPTH:
        return
    try:
        children = sorted((p for p in base.iterdir() if p.is_dir() and not p.is_symlink()), key=lambda p: p.name)
    except OSError:
        return
    for child in children:
        rel = child.relative_to(root).as_posix()
        entry = classify(rel, known)
        if entry and entry.get("skip"):
            continue
        if entry and entry["layer"] != "asset":
            yield child, rel, entry
        else:
            yield from walk_nested(root, child, known, depth + 1)


def measure(path: Path, heavy: bool, full: bool) -> dict:
    if path.is_symlink():
        return {"bytes": None, "files": None, "newest": None, "symlink": True}
    if path.is_file():
        st = path.lstat()
        return {"bytes": st.st_size, "files": 1, "newest": st.st_mtime}
    if heavy and not full:
        return {"bytes": None, "files": None, "newest": None, "skipped": "依赖目录，使用 --full 统计"}
    total = count = 0
    newest = path.lstat().st_mtime
    truncated = False
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in files:
            try:
                st = (Path(base) / name).lstat()
            except OSError:
                continue
            total += st.st_size
            count += 1
            newest = max(newest, st.st_mtime)
            if count >= MAX_FILES:
                truncated = True
                break
        if truncated:
            break
    result = {"bytes": total, "files": count, "newest": newest}
    if truncated:
        result["truncated"] = True
    return result


def process_refs() -> list[tuple[int, list[str]]] | None:
    proc = Path("/proc")
    if not proc.is_dir():
        return None
    found = []
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
            found.append((int(item.name), refs))
        except (OSError, ProcessLookupError):
            continue
    return found


def active_pids(path: Path, procs) -> list[int] | None:
    if procs is None:
        return None
    target = str(path)
    return sorted(pid for pid, refs in procs if any(r == target or r.startswith(target + "/") for r in refs))


def references(root: Path, rel: str, is_dir: bool) -> list[str]:
    needle = rel + "/" if is_dir else rel
    hits = split0(git(root, "grep", "-I", "-l", "-z", "-F", "-e", needle))
    return [h for h in hits if not (h == rel or h.startswith(rel + "/"))][:MAX_REFS]


def iso(ts: float | None) -> str | None:
    return None if ts is None else datetime.fromtimestamp(ts, timezone.utc).astimezone().isoformat(timespec="seconds")


def scan(root: Path, full: bool) -> dict:
    known = load_known()
    in_git = git(root, "rev-parse", "--is-inside-work-tree") is not None
    tracked = split0(git(root, "ls-files", "-z")) if in_git else []
    untracked = split0(git(root, "ls-files", "-z", "--others", "--exclude-standard")) if in_git else []
    tracked_ignored = split0(git(root, "ls-files", "-z", "-ci", "--exclude-standard")) if in_git else []
    procs = process_refs()
    candidates = list(walk_candidates(root, known))

    ignored_by: dict[str, str] = {}
    if in_git and candidates:
        query = b"".join((rel + ("/" if p.is_dir() else "")).encode() + b"\0" for p, rel, _ in candidates)
        # 输出按 source、linenum、pattern、pathname 四元组排列；未命中时前三项为空串。
        raw = (git(root, "check-ignore", "-v", "-n", "-z", "--no-index", "--stdin", stdin=query) or b"").decode("utf-8", "replace").split("\0")
        for i in range(0, len(raw) - 3, 4):
            source, line, pattern, pathname = raw[i:i + 4]
            if pattern:
                ignored_by[pathname.rstrip("/")] = f"{source}:{line}:{pattern}"

    entries = []
    for path, rel, entry in candidates:
        is_dir = path.is_dir() and not path.is_symlink()
        prefix = rel + "/"
        n_tracked = sum(1 for t in tracked if t == rel or t.startswith(prefix))
        n_untracked = sum(1 for u in untracked if u == rel or u.startswith(prefix))
        n_tracked_ignored = sum(1 for t in tracked_ignored if t == rel or t.startswith(prefix))
        layer = entry["layer"] if entry else "unknown"
        info = {
            "path": rel,
            "kind": "dir" if is_dir else ("symlink" if path.is_symlink() else "file"),
            "layer_guess": layer,
            "ignore_guess": entry["ignore"] if entry else "ask",
            "matched": entry["match"] if entry else None,
            "note": entry.get("note") if entry else None,
            "migrate_to": entry.get("migrate_to") if entry else None,
            "tracked_files": n_tracked if in_git else None,
            "untracked_unignored_files": n_untracked if in_git else None,
            "ignored_by": ignored_by.get(rel),
            **measure(path, bool(entry and entry.get("heavy")), full),
            "active_pids": active_pids(path.resolve(), procs),
            "referenced_by": references(root, rel, is_dir) if in_git and layer not in ("asset",) else [],
        }
        info["newest"] = iso(info["newest"])
        questions, actions = [], []
        if layer == "ask":
            questions.append("常见但用途有歧义，需确认归属与是否忽略")
        if layer == "unknown" and (not in_git or n_tracked == 0 or n_untracked > 0):
            questions.append("未知用途，需确认归属")
        if "/" in rel and layer == "local":
            questions.append("模块内的本机状态目录，确认保留原位或并入根 .local/")
        if n_tracked_ignored:
            questions.append(f"{n_tracked_ignored} 个已跟踪文件命中忽略规则，确认应跟踪还是移出版本库")
        if layer == "unknown" and n_tracked and not n_untracked:
            info["layer_guess"], info["ignore_guess"] = "asset", "no"
        if layer in ("work", "local", "program", "secret", "legacy") and n_untracked:
            actions.append("产物未被忽略，补 .gitignore 规则")
        if layer == "legacy":
            actions.append(f"迁移到 {info['migrate_to']}")
            if info["referenced_by"]:
                actions.append("迁移时更新引用")
        if info["active_pids"] and (questions or actions):
            actions.append("正被进程使用，停止后再处理")
        info["questions"], info["actions"] = questions, actions
        if "/" in rel and layer == "program" and info["ignored_by"] and not questions and not actions:
            continue
        entries.append(info)
    return {
        "root": str(root),
        "scanned_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "git": in_git,
        "process_check": procs is not None,
        "entries": entries,
        "tracked_but_ignored": tracked_ignored[:200],
        "tracked_but_ignored_total": len(tracked_ignored),
        "summary": {
            "entries": len(entries),
            "questions": sum(1 for e in entries if e["questions"]),
            "actions": sum(1 for e in entries if e["actions"]),
        },
    }


def human(n: int | None) -> str:
    if n is None:
        return "-"
    for unit in ("B", "K", "M", "G"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}T"


def to_markdown(report: dict) -> str:
    rows = ["| 路径 | 分类猜测 | 忽略建议 | 跟踪/未忽略 | 命中规则 | 大小 | 最近修改 | 引用 | 占用 | 待确认 | 动作 |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in report["entries"]:
        rows.append("| " + " | ".join([
            f"`{e['path']}`", e["layer_guess"], e["ignore_guess"],
            f"{e['tracked_files']}/{e['untracked_unignored_files']}",
            f"`{e['ignored_by']}`" if e["ignored_by"] else "-",
            human(e["bytes"]), (e["newest"] or "-")[:10],
            "<br>".join(e["referenced_by"]) or "-",
            ",".join(map(str, e["active_pids"] or [])) or "-",
            "<br>".join(e["questions"]) or "-",
            "<br>".join(e["actions"]) or "-",
        ]) + " |")
    lines = [f"# 工作区扫描：{report['root']}", "", f"扫描时间：{report['scanned_at']}；Git：{report['git']}；进程检查：{report['process_check']}", "",
             f"条目 {report['summary']['entries']}，待确认 {report['summary']['questions']}，待处理 {report['summary']['actions']}。", "", *rows]
    if report["tracked_but_ignored_total"]:
        lines += ["", f"## 已跟踪但命中忽略规则的文件（{report['tracked_but_ignored_total']}）", ""]
        lines += [f"- `{p}`" for p in report["tracked_but_ignored"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="工作区根目录，默认取当前目录所在 Git 仓库根")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--full", action="store_true", help="统计依赖目录大小")
    args = parser.parse_args()
    if args.root:
        root = Path(args.root)
    else:
        top = git(Path.cwd(), "rev-parse", "--show-toplevel")
        root = Path(top.decode().strip()) if top else Path.cwd()
    root = root.resolve()
    if not root.is_dir():
        print(f"不是目录：{root}", file=sys.stderr)
        return 2
    report = scan(root, args.full)
    sys.stdout.write(to_markdown(report) if args.format == "md" else json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
