"""Storage analyzer paths and command-line options."""
import argparse
import os
import stat
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]

def storage_dir(kind, explicit=None):
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = 'LLM_SKILLS_DATA_DIR' if kind == 'data' else 'LLM_SKILLS_STATE_DIR'
    if os.environ.get(env):
        return Path(os.environ[env]).expanduser().resolve() / 'storage-analyzer'
    home = Path.home().resolve()
    for parent in [SKILL, *SKILL.parents]:
        if (parent / '.git').exists():
            return parent / ('data' if kind == 'data' else '.local') / 'storage-analyzer'
        if parent == home:
            break
    return home / '.llm-skills' / ('data' if kind == 'data' else 'local') / 'storage-analyzer'

def parser(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument('--output', help='扫描及报告目录；读取已有扫描时必填')
    return p

def existing_output(args):
    if not args.output:
        raise ValueError('请用 --output 指定已完成的扫描目录')
    return storage_dir('data', args.output)

REPARSE = 0x400
OFFLINE = 0x1000 | 0x40000 | 0x400000


def _inside(path, profile, scan_root):
    if len(path.drive) != 2 or not path.is_absolute() or '..' in path.parts:
        raise ValueError('目标必须为规范绝对路径')
    for root in (Path(profile), Path(scan_root)):
        if path == root or not path.is_relative_to(root):
            raise ValueError('目标超出用户目录或扫描范围')


def _plain_chain(folder, checked):
    """Reject reparse points on a directory and its ancestors; `checked` caches verified directories."""
    seen = []
    for item in [folder, *folder.parents[:-1]]:
        key = str(item).lower()
        if checked is not None and key in checked:
            break
        if getattr(item.lstat(), 'st_file_attributes', 0) & REPARSE:
            raise ValueError('目标或父目录是重解析点')
        seen.append(key)
    if checked is not None:
        checked.update(seen)


def guarded_path(record, profile, scan_root, checked=None):
    """Accept unchanged local regular files below both approved roots."""
    path = Path(record['path'])
    _inside(path, profile, scan_root)
    _plain_chain(path.parent, checked)
    st = path.lstat()
    attrs = getattr(st, 'st_file_attributes', 0)
    if attrs & REPARSE:
        raise ValueError('目标或父目录是重解析点')
    if not stat.S_ISREG(st.st_mode) or st.st_size != record['size'] or st.st_mtime != record['mtime']:
        raise ValueError('文件自扫描后已变化，请重新扫描')
    if attrs & OFFLINE:
        raise ValueError('跳过离线或云端文件')
    return str(path)


def guarded_dir(folder, profile, scan_root, checked=None):
    """Accept a plain local directory below both approved roots."""
    path = Path(folder)
    _inside(path, profile, scan_root)
    _plain_chain(path, checked)
    if not path.is_dir():
        raise ValueError('目录已不存在')
    return str(path)
