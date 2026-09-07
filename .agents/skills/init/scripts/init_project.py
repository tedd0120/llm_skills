#!/usr/bin/env python3
"""
一键初始化新项目的 AGENTS.md 与 CLAUDE.md，支持新建初始化与存量查漏补缺。
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


def parse_sections(md_text: str) -> list[tuple[str, str]]:
    """解析 Markdown 中的二级标题板块，返回 (title, full_block) 列表。"""
    sections = []
    current_title = ""
    current_lines = []

    for line in md_text.splitlines():
        if line.startswith("## "):
            if current_title:
                sections.append(
                    (current_title, f"## {current_title}\n\n" + "\n".join(current_lines).strip())
                )
            current_title = line[3:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections.append(
            (current_title, f"## {current_title}\n\n" + "\n".join(current_lines).strip())
        )
    return sections


SECTION_KEYWORDS = {
    "语言": ["语言", "简体中文"],
    "Git 操作": ["git 操作", "git safety", "git 安全"],
    "任务规划与执行状态": ["docs/plans", "plans/", "任务规划", "执行状态"],
    "原型产物": [".prototype", "prototype"],
    "代码检索": ["codegraph", "代码检索", "代码定位"],
    "Skill 规范": ["skill 规范", "渐进式披露", "references/"],
}


def section_is_covered(existing_text: str, title: str) -> bool:
    """检查既有内容是否已覆盖某个通用规则板块。"""
    lower_text = existing_text.lower()
    keywords = SECTION_KEYWORDS.get(title, [title.lower()])
    return any(kw.lower() in lower_text for kw in keywords)


def audit_and_patch_agents_md(agents_md: Path, agents_tpl: str) -> None:
    """对既有 AGENTS.md 进行查漏补缺，不强行覆盖既有规则。"""
    content = agents_md.read_text(encoding="utf-8")
    tpl_sections = parse_sections(agents_tpl)

    missing_sections = []
    for title, block in tpl_sections:
        if not section_is_covered(content, title):
            missing_sections.append((title, block))

    if not missing_sections:
        print("[完备] AGENTS.md 既有规则已包含全部通用规范，无需补充")
        return

    print(f"[增量补齐] AGENTS.md 缺少 {len(missing_sections)} 项通用规则:")
    for title, _ in missing_sections:
        print(f"  + 补齐板块: ## {title}")

    separator = "" if content.endswith("\n\n") else ("\n" if content.endswith("\n") else "\n\n")
    patch_text = "\n\n".join(block for _, block in missing_sections) + "\n"
    agents_md.write_text(content + separator + patch_text, encoding="utf-8")
    print(f"[更新] AGENTS.md 已成功追加缺失板块")


def audit_and_patch_claude_md(claude_md: Path, claude_tpl: str) -> None:
    """对既有 CLAUDE.md 进行单真源检查，缺失时前置追加引用。"""
    content = claude_md.read_text(encoding="utf-8")
    if "@AGENTS.md" in content or "@agents.md" in content:
        print("[完备] CLAUDE.md 已包含 @AGENTS.md 引用声明")
    else:
        print("[增量补齐] CLAUDE.md 未引用 @AGENTS.md，正在前置注入引用声明")
        claude_md.write_text(claude_tpl.strip() + "\n\n" + content, encoding="utf-8")
        print("[更新] CLAUDE.md 已成功注入单真源声明")


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

    # 1. 处理 CLAUDE.md
    if not claude_md.exists():
        claude_md.write_text(claude_tpl, encoding="utf-8")
        print(f"[新建] {claude_md.name}")
    elif force:
        claude_md.write_text(claude_tpl, encoding="utf-8")
        print(f"[覆盖] {claude_md.name} (已强制重置)")
    else:
        audit_and_patch_claude_md(claude_md, claude_tpl)

    # 2. 处理 AGENTS.md
    if not agents_md.exists():
        agents_md.write_text(agents_tpl, encoding="utf-8")
        print(f"[新建] {agents_md.name}")
    elif force:
        agents_md.write_text(agents_tpl, encoding="utf-8")
        print(f"[覆盖] {agents_md.name} (已强制重置)")
    else:
        audit_and_patch_agents_md(agents_md, agents_tpl)

    # 3. 创建 docs/plans/
    plans_dir.mkdir(parents=True, exist_ok=True)
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"[创建] docs/plans/.gitkeep")
    else:
        print(f"[保持] docs/plans/ 目录已就绪")

    # 4. 配置 .gitignore
    prototype_rule = ".prototype/\n"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".prototype/" not in content and ".prototype" not in content:
            separator = "" if content.endswith("\n") or not content else "\n"
            gitignore.write_text(content + separator + prototype_rule, encoding="utf-8")
            print(f"[更新] .gitignore (追加 .prototype/)")
        else:
            print(f"[保持] .gitignore 已包含 .prototype 规则")
    else:
        gitignore.write_text(prototype_rule, encoding="utf-8")
        print(f"[创建] .gitignore (添加 .prototype/)")

    print("\n项目规则检查与初始化完成！")


if __name__ == "__main__":
    is_explicit = len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    target_path = Path(sys.argv[1]) if is_explicit else Path.cwd()
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    root = find_repo_root(target_path, is_explicit=is_explicit)
    init_project(root, force=force_flag)
