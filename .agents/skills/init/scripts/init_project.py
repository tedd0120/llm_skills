#!/usr/bin/env python3
"""
一键初始化新项目的 AGENTS.md 与 CLAUDE.md。
"""

import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def find_repo_root(start_dir: Path, is_explicit: bool = False) -> Path:
    current = start_dir.resolve()
    if is_explicit or (current / ".git").exists():
        return current
    home = Path.home().resolve()
    for parent in current.parents:
        if parent == home or parent == parent.parent:
            break
        if (parent / ".git").exists():
            return parent
    return current


def init_project(target_dir: Path, force: bool = False) -> None:
    root = find_repo_root(target_dir)
    print(f"目标项目根目录: {root}")

    claude_md = root / "CLAUDE.md"
    agents_md = root / "AGENTS.md"
    plans_dir = root / "docs" / "plans"
    gitkeep = plans_dir / ".gitkeep"
    gitignore = root / ".gitignore"

    claude_tpl = (TEMPLATES_DIR / "CLAUDE.md").read_text(encoding="utf-8")
    agents_tpl = (TEMPLATES_DIR / "AGENTS.md").read_text(encoding="utf-8")

    # 1. 写入 CLAUDE.md
    if claude_md.exists() and not force:
        print(f"[跳过] {claude_md.name} 已存在")
    else:
        claude_md.write_text(claude_tpl, encoding="utf-8")
        print(f"[创建] {claude_md.name}")

    # 2. 写入 AGENTS.md
    if agents_md.exists() and not force:
        print(f"[跳过] {agents_md.name} 已存在")
    else:
        agents_md.write_text(agents_tpl, encoding="utf-8")
        print(f"[创建] {agents_md.name}")

    # 3. 创建 docs/plans/
    plans_dir.mkdir(parents=True, exist_ok=True)
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"[创建] docs/plans/.gitkeep")

    # 4. 配置 .gitignore
    prototype_rule = ".prototype/\n"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".prototype/" not in content and ".prototype" not in content:
            separator = "" if content.endswith("\n") or not content else "\n"
            gitignore.write_text(content + separator + prototype_rule, encoding="utf-8")
            print(f"[更新] .gitignore (追加 .prototype/)")
        else:
            print(f"[跳过] .gitignore 已包含 .prototype 规则")
    else:
        gitignore.write_text(prototype_rule, encoding="utf-8")
        print(f"[创建] .gitignore (添加 .prototype/)")

    print("\n初始化完成！")


if __name__ == "__main__":
    is_explicit = len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    target_path = Path(sys.argv[1]) if is_explicit else Path.cwd()
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    root = find_repo_root(target_path, is_explicit=is_explicit)
    init_project(root, force=force_flag)
