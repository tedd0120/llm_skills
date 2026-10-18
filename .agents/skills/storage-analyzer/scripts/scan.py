"""Read-only metadata scan of a Windows drive or directory into inventory.sqlite."""
import ctypes
import json
import os
import shutil
import sqlite3
import string
import time
from datetime import datetime
from pathlib import Path

from common import parser, storage_dir

REPARSE = 0x400


def fixed_drives():
    """Local fixed drives with capacity, used for migration suggestions."""
    drives = []
    for letter in string.ascii_uppercase:
        root = letter + ':' + os.sep
        if ctypes.windll.kernel32.GetDriveTypeW(root) != 3:
            continue
        try:
            usage = shutil.disk_usage(root)
        except OSError:
            continue
        drives.append(dict(drive=letter + ':', total=usage.total, free=usage.free))
    return drives


def main():
    p = parser('只读扫描 Windows 磁盘或目录')
    p.add_argument('--root', default=os.environ.get('SystemDrive', 'C:') + os.sep)
    args = p.parse_args()
    if os.name != 'nt':
        raise SystemExit('当前扫描器支持 Windows')
    root = Path(os.path.abspath(args.root))
    if len(root.drive) != 2 or not root.is_dir() or root.lstat().st_file_attributes & REPARSE:
        raise SystemExit('扫描根必须是普通本地目录')
    base = storage_dir('data', args.output) if args.output else storage_dir('data') / datetime.now().strftime('%Y%m%d_%H%M%S')
    base.mkdir(parents=True, exist_ok=True)
    if (base / 'inventory.sqlite').exists():
        raise SystemExit('该目录已有扫描，请指定新输出目录')
    db = sqlite3.connect(base / 'inventory.sqlite')
    db.execute('CREATE TABLE files(path TEXT PRIMARY KEY, size INTEGER, mtime REAL, attrs INTEGER)')
    stack = [str(root)]
    errors, links, batch = [], [], []
    count = 0
    started = time.time()
    while stack:
        folder = stack.pop()
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    if Path(entry.path) == base:
                        continue
                    try:
                        st = entry.stat(follow_symlinks=False)
                        attrs = getattr(st, 'st_file_attributes', 0)
                        if attrs & REPARSE:
                            links.append(entry.path)
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            batch.append((entry.path, st.st_size, st.st_mtime, attrs))
                            count += 1
                            if len(batch) >= 10000:
                                db.executemany('INSERT OR IGNORE INTO files VALUES (?,?,?,?)', batch)
                                db.commit()
                                batch.clear()
                                print(f'{count:,} files; {time.time()-started:.0f}s; {folder}', flush=True)
                    except OSError as exc:
                        errors.append({'path': entry.path, 'error': str(exc)})
        except OSError as exc:
            errors.append({'path': folder, 'error': str(exc)})
    db.executemany('INSERT OR IGNORE INTO files VALUES (?,?,?,?)', batch)
    db.commit()
    db.close()
    usage = shutil.disk_usage(root)
    meta = dict(root=str(root), profile=str(Path.home()), started=started, finished=time.time(), count=count,
                errors=errors, skipped_reparse=links, disk=dict(total=usage.total, used=usage.used, free=usage.free),
                drives=fixed_drives())
    (base / 'scan-meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in meta.items() if k not in ('errors', 'skipped_reparse')}), flush=True)
    print('OUTPUT=' + str(base), flush=True)


if __name__ == '__main__':
    main()
