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
    "任务规划与执行状态": ["任务规划", "执行状态", "plan.md"],
    "工作区与产物目录": [".work/", "任务工作区"],
    "代码检索": ["codegraph", "代码检索", "代码定位"],
    "Skill 规范": ["skill 规范", "渐进式披露", "references/"],
}


LEGACY_MARKERS = ("docs/plans", ".prototype/", ".prototypes/", ".tmp/")
LAYOUT_SECTIONS = ("任务规划与执行状态", "工作区与产物目录")
IGNORE_RULES = (".work/", ".local/")


def uses_legacy_layout(existing_text: str) -> bool:
    """既有规则仍采用旧产物目录且尚未切换到 .work/ 布局。"""
    return ".work/" not in existing_text and any(m in existing_text for m in LEGACY_MARKERS)


def section_is_covered(existing_text: str, title: str) -> bool:
    """检查既有内容是否已覆盖某个通用规则板块。"""
    lower_text = existing_text.lower()
    keywords = SECTION_KEYWORDS.get(title, [title.lower()])
    return any(kw.lower() in lower_text for kw in keywords)


def audit_and_patch_agents_md(agents_md: Path, agents_tpl: str) -> None:
    """对既有 AGENTS.md 进行查漏补缺，不强行覆盖既有规则。"""
    content = agents_md.read_text(encoding="utf-8")
    tpl_sections = parse_sections(agents_tpl)

    legacy = uses_legacy_layout(content)
    missing_sections = []
    for title, block in tpl_sections:
        if legacy and title in LAYOUT_SECTIONS:
            continue
        if not section_is_covered(content, title):
            missing_sections.append((title, block))
    if legacy:
        print("[提示] AGENTS.md 仍使用旧产物目录（docs/plans、.prototype 等），未追加工作区板块；请使用 workspace-layout skill 迁移")

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

    # 3. 配置 .gitignore
    content = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    present = {line.strip() for line in content.splitlines()}
    missing = [rule for rule in IGNORE_RULES if rule not in present and rule.rstrip("/") not in present]
    if missing:
        separator = "" if content.endswith("\n") or not content else "\n"
        gitignore.write_text(content + separator + "".join(f"{rule}\n" for rule in missing), encoding="utf-8")
        print(f"[更新] .gitignore (追加 {' '.join(missing)})")
    else:
        print("[保持] .gitignore 已包含 .work/ 与 .local/ 规则")

    print("\n项目规则检查与初始化完成！")


if __name__ == "__main__":
    is_explicit = len(sys.argv) > 1 and not sys.argv[1].startswith("-")
    target_path = Path(sys.argv[1]) if is_explicit else Path.cwd()
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    root = find_repo_root(target_path, is_explicit=is_explicit)
    init_project(root, force=force_flag)
