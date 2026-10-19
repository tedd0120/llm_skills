"""Resolve this skill's artifacts and local state independently of cwd."""
import os
from pathlib import Path

NAME = '360teams-proxy-repair'


def directory(kind, explicit=None):
    if explicit:
        return Path(explicit).expanduser().resolve()
    variable = 'LLM_SKILLS_STATE_DIR' if kind == 'state' else 'LLM_SKILLS_DATA_DIR'
    if os.environ.get(variable):
        return Path(os.environ[variable]).expanduser().resolve() / NAME
    for parent in Path(__file__).resolve().parents:
        if (parent / '.git').exists():
            return parent / ('.local' if kind == 'state' else 'data') / NAME
        if parent == Path.home():
            break
    return Path.home() / '.llm-skills' / ('local' if kind == 'state' else 'data') / NAME
