"""Storage analyzer paths and command-line options."""
import argparse
import os
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

def guarded_path(record, profile, scan_root):
    """Accept unchanged local regular files below both approved roots."""
    path = Path(record['path'])
    if len(path.drive)!=2 or not path.is_absolute() or '..' in path.parts:
        raise ValueError('目标必须为规范绝对路径')
    for root in (Path(profile), Path(scan_root)):
        if path == root or not path.is_relative_to(root):
            raise ValueError('目标超出用户目录或扫描范围')
    for item in [path, *path.parents[:-1]]:
        if item.is_symlink() or getattr(item.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('目标或父目录是重解析点')
    st = path.stat()
    if not path.is_file() or st.st_size != record['size'] or st.st_mtime != record['mtime']:
        raise ValueError('文件自扫描后已变化，请重新扫描')
    if getattr(st, 'st_file_attributes', 0) & (0x1000 | 0x40000 | 0x400000):
        raise ValueError('跳过离线或云端文件')
    return str(path)
