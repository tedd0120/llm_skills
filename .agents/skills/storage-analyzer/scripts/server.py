"""Local-only cleanup service for a storage-analyzer report."""
import base64
import ctypes
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

import pythoncom
from win32com.shell import shell, shellcon
from send2trash.win.IFileOperationProgressSink import FileOperationProgressSink
from win32com.server.exception import COMException

from common import parser, existing_output, storage_dir, guarded_path

SAFE = '优先清理'
p = parser('启动仅本机可访问的清理服务')
p.add_argument('--port', type=int, default=0, help='0 表示随机空闲端口')
p.add_argument('--state-dir')
args = p.parse_args()
BASE = existing_output(args)
STATE = storage_dir('state', args.state_dir)
STATE.mkdir(parents=True, exist_ok=True)
PORT = args.port
ORIGIN = f'http://127.0.0.1:{PORT}'
TOKEN = secrets.token_urlsafe(32)
MANIFEST = json.loads((BASE / 'manifest.json').read_text(encoding='utf-8'))
REPORT = json.loads((BASE / 'report-data.json').read_text(encoding='utf-8')) if (BASE / 'report-data.json').exists() else {}
GROUPS = {g['id']: g for g in MANIFEST['groups']}
DRIVE = Path(MANIFEST['root']).drive + '\\'
if Path(MANIFEST['profile']).resolve() != Path.home().resolve():
    raise SystemExit('扫描属于另一用户，请在当前账户重新扫描')
DONE_FILE = BASE / 'cleaned.json'
DONE = json.loads(DONE_FILE.read_text(encoding='utf-8')) if DONE_FILE.exists() else {}
START_FREE = shutil.disk_usage(DRIVE).free
JOB = {'running': False}
LOCK = threading.Lock()
SYSTEM_JOB = {}


def validate(record):
    return guarded_path(record, Path.home(), MANIFEST['root'])


def openable_paths():
    """Every path the report displays may be opened in Explorer."""
    paths = {g['root'] for g in MANIFEST['groups']}
    paths |= {f['path'] for g in REPORT.get('groups', []) for f in g.get('samples', [])}
    paths |= {r['path'] for r in REPORT.get('review', [])} | {r['path'] for r in REPORT.get('largest', [])}
    paths |= {m['path'] for m in REPORT.get('moves', {}).get('items', [])}
    paths |= {part[0] for c in REPORT.get('system', []) for part in c.get('parts', [])}
    stack = [REPORT['tree']] if REPORT.get('tree') else []
    while stack:
        node = stack.pop()
        paths.add(node['p'])
        stack.extend(node.get('c', []))
    return {x.lower() for x in paths}


OPENABLE = openable_paths()


class RecycleSink(FileOperationProgressSink):
    def __init__(self, records):
        super().__init__()
        self.records = {r['path'].lower(): r for r in records}
        self.results = []

    def PreDeleteItem(self, flags, item):
        if not flags & shellcon.TSF_DELETE_RECYCLE_IF_POSSIBLE:
            raise COMException('只允许放进回收站', scode=-2147467259)
        path = item.GetDisplayName(shellcon.SIGDN_FILESYSPATH)
        try:
            validate(self.records[path.lower()])
        except Exception as exc:
            raise COMException(str(exc), scode=-2147467259)
        return 0

    def PostDeleteItem(self, flags, item, result, new_item):
        path = item.GetDisplayName(shellcon.SIGDN_FILESYSPATH)
        self.results.append({'path': path, 'ok': 0 <= result < 0x80000000 and new_item is not None,
                             'result': result, 'recycle_path': new_item.GetDisplayName(shellcon.SIGDN_FILESYSPATH) if new_item else None})
        return 0


def recycle(records):
    pythoncom.CoInitialize()
    sink = RecycleSink(records)
    error = None
    try:
        operation = pythoncom.CoCreateInstance(shell.CLSID_FileOperation, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IFileOperation)
        operation.SetOperationFlags(0x20000000 | 0x00080000 | shellcon.FOFX_EARLYFAILURE | shellcon.FOF_NOERRORUI | shellcon.FOF_NOCONFIRMATION | shellcon.FOF_SILENT)
        wrapped = pythoncom.WrapObject(sink, shell.IID_IFileOperationProgressSink)
        for r in records:
            item = shell.SHCreateItemFromParsingName(validate(r), None, shell.IID_IShellItem)
            operation.DeleteItem(item, wrapped)
        result = operation.PerformOperations()
        if result or operation.GetAnyOperationsAborted():
            error = f'系统取消或部分文件无法回收：{result}'
    except Exception as exc:
        error = str(exc)
    finally:
        pythoncom.CoUninitialize()
    return sink.results, error


def delete(records):
    """Permanently remove regenerable cache files; returns per-file results."""
    results = []
    for r in records:
        try:
            path = validate(r)
            try:
                os.remove(path)
            except PermissionError:
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
            results.append({'path': path, 'ok': True})
        except Exception as exc:
            results.append({'path': r['path'], 'ok': False, 'error': str(exc)})
    return results


def note_error(path, error):
    JOB['skipped'] += 1
    if len(JOB['errors']) < 2000:
        JOB['errors'].append({'path': path, 'error': error})


def run_job(groups, mode):
    try:
        for group in groups:
            JOB['current'] = group['title']
            before = JOB['bytes']
            skipped_before = JOB['skipped']
            files = group['files']
            for start in range(0, len(files), 100):
                chunk = []
                for r in files[start:start + 100]:
                    try:
                        validate(r)
                        chunk.append(r)
                    except Exception as exc:
                        note_error(r['path'], str(exc))
                if mode == 'delete':
                    results, error = delete(chunk), None
                    failed = {x['path'].lower(): x.get('error') for x in results if not x['ok']}
                else:
                    results, error = recycle(chunk) if chunk else ([], None)
                    succeeded = {x['path'].lower() for x in results if x['ok']}
                    failed = {r['path'].lower(): error or '未获得回收站成功回执' for r in chunk if r['path'].lower() not in succeeded}
                for r in chunk:
                    if r['path'].lower() in failed:
                        note_error(r['path'], failed[r['path'].lower()])
                    else:
                        JOB['done_files'] += 1
                        JOB['bytes'] += r['size']
                JOB['processed'] += len(files[start:start + 100])
                with (BASE / 'operations.jsonl').open('a', encoding='utf-8') as f:
                    f.write(json.dumps({'time': time.time(), 'group': group['id'], 'mode': mode, 'results': results, 'error': error}, ensure_ascii=False) + '\n')
            freed = JOB['bytes'] - before
            DONE[group['id']] = dict(mode=mode, bytes=freed, skipped=JOB['skipped'] - skipped_before, time=time.time())
            DONE_FILE.write_text(json.dumps(DONE, ensure_ascii=False), encoding='utf-8')
    except Exception as exc:
        JOB['errors'].append({'error': str(exc)})
    finally:
        JOB['running'] = False
        JOB['current'] = None
        RECYCLE['wake'].set()
        with (BASE / 'operations.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps({'time': time.time(), 'summary': {k: v for k, v in JOB.items() if k != 'errors'},
                                'errors': JOB['errors'][:200]}, ensure_ascii=False) + '\n')


class RecycleInfo(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD), ('i64Size', ctypes.c_longlong), ('i64NumItems', ctypes.c_longlong)]


def recycle_bin():
    info = RecycleInfo(ctypes.sizeof(RecycleInfo), 0, 0)
    if ctypes.windll.shell32.SHQueryRecycleBinW(DRIVE, ctypes.byref(info)) != 0:
        return None
    return {'size': info.i64Size, 'items': info.i64NumItems}


RECYCLE = {'info': None, 'wake': threading.Event()}


def watch_recycle_bin():
    """Querying a large recycle bin takes seconds; refresh it off the request path."""
    while True:
        try:
            RECYCLE['info'] = recycle_bin()
        except OSError:
            RECYCLE['info'] = None
        RECYCLE['wake'].wait(15)
        RECYCLE['wake'].clear()


def run_elevated(executable, parameters):
    code = ctypes.windll.shell32.ShellExecuteW(None, 'runas', executable, parameters, None, 1)
    if code <= 32:
        raise RuntimeError('管理员授权被取消或启动失败')


def powershell_elevated(script):
    script += "\nWrite-Host ''; Write-Host '已完成，可以关闭此窗口。'"
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    run_elevated('powershell.exe', f'-NoProfile -NoExit -ExecutionPolicy Bypass -EncodedCommand {encoded}')


def old_update_dirs():
    windows = Path(os.environ.get('SystemRoot', DRIVE + 'Windows'))
    return [d for d in windows.iterdir() if re.fullmatch(r'SoftwareDistribution\.old\.\d+', d.name, re.I)
            and d.is_dir() and not d.lstat().st_file_attributes & 0x400] if windows.drive.lower() == DRIVE[:2].lower() else []


def empty_recycle():
    SYSTEM_JOB['empty-recycle'] = 'running'
    try:
        # Flags 0 keeps the Windows confirmation dialog.
        result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, DRIVE, 0)
        SYSTEM_JOB['empty-recycle'] = 'done' if result == 0 else 'cancelled'
    except Exception:
        SYSTEM_JOB['empty-recycle'] = 'failed'
    RECYCLE['wake'].set()


def system_action(action):
    if action == 'open-recycle':
        os.startfile('shell:RecycleBinFolder')
    elif action == 'empty-recycle':
        if SYSTEM_JOB.get('empty-recycle') == 'running':
            raise RuntimeError('Windows 确认框已打开，请在任务栏中找到它')
        threading.Thread(target=empty_recycle, daemon=True).start()
    elif action == 'storage-settings':
        os.startfile('ms-settings:storagesense')
    elif action == 'apps-settings':
        os.startfile('ms-settings:appsfeatures')
    elif action == 'virtual-memory':
        subprocess.Popen(['SystemPropertiesPerformance.exe'])
    elif action == 'cleanmgr':
        run_elevated('cleanmgr.exe', '/d ' + DRIVE[:2])
    elif action == 'dism-cleanup':
        powershell_elevated('Dism.exe /Online /Cleanup-Image /StartComponentCleanup')
    elif action == 'hibernate-reduced':
        run_elevated('powercfg.exe', '/h /type reduced')
    elif action == 'hibernate-off':
        run_elevated('powercfg.exe', '/h off')
    elif action == 'remove-sd-old':
        targets = old_update_dirs()
        if not targets:
            raise RuntimeError('没有找到旧更新目录')
        powershell_elevated('\n'.join(f"Remove-Item -LiteralPath '{d}' -Recurse -Force" for d in targets))
    else:
        raise ValueError('未知操作')


ALLOWED_ACTIONS = {a['id'] for c in REPORT.get('system', []) for a in c.get('actions', [])}


def open_in_explorer(path):
    if path.lower() not in OPENABLE:
        raise ValueError('只能打开报告中列出的位置')
    target = Path(path)
    if target.is_file():
        subprocess.Popen(f'explorer /select,"{target}"')
    elif target.is_dir():
        os.startfile(target)
    else:
        raise ValueError('该位置已不存在')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, status, data, content_type='application/json; charset=utf-8'):
        raw = data.encode('utf-8') if isinstance(data, str) else json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.headers.get('Host') != f'127.0.0.1:{PORT}':
            return self.reply(403, {'error': 'Host 校验失败'})
        route = urlsplit(self.path).path
        if route == '/':
            page = BASE / 'report.html'
            html = page.read_text(encoding='utf-8') if page.exists() else '<p>请先运行 build_report.py</p>'
            return self.reply(200, html.replace('__SESSION_TOKEN__', TOKEN), 'text/html; charset=utf-8')
        if self.headers.get('X-Cleanup-Token') != TOKEN:
            return self.reply(403, {'error': '请从本机报告入口访问'})
        if route == '/api/status':
            job = {k: v for k, v in JOB.items() if k != 'errors'}
            job['error_count'] = len(JOB.get('errors', []))
            return self.reply(200, {'disk': shutil.disk_usage(DRIVE)._asdict(), 'start_free': START_FREE, 'recycle': RECYCLE['info'],
                                    'job': job, 'done': DONE, 'system': SYSTEM_JOB})
        if route == '/api/job':
            return self.reply(200, JOB)
        if route.startswith('/api/files/'):
            group = GROUPS.get(route.rsplit('/', 1)[-1])
            if group:
                return self.reply(200, group['files'])
        self.reply(404, {'error': '未找到'})

    def do_POST(self):
        global JOB
        if self.headers.get('Host') != f'127.0.0.1:{PORT}' or self.headers.get('Origin') != ORIGIN or self.headers.get('X-Cleanup-Token') != TOKEN:
            return self.reply(403, {'error': '本机来源或会话校验失败'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16384:
                raise ValueError('请求长度无效')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('请求必须为对象')
            route = urlsplit(self.path).path
            if route == '/api/open':
                open_in_explorer(str(data.get('path', '')))
                return self.reply(200, {'ok': True})
            if data.get('confirmed') is not True:
                raise ValueError('请先在页面上确认')
            if route == '/api/system':
                if data.get('action') not in ALLOWED_ACTIONS:
                    raise ValueError('该操作不适用于本次扫描')
                system_action(data['action'])
                return self.reply(200, {'ok': True})
            if route != '/api/clean':
                raise ValueError('未知接口')
            ids, mode = data.get('ids'), data.get('mode', 'recycle')
            if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or not all(isinstance(i, str) for i in ids):
                raise ValueError('请选择要清理的文件群')
            groups = [GROUPS.get(i) for i in ids]
            if not all(g and g['enabled'] for g in groups):
                raise ValueError('包含不可清理的文件群')
            if mode not in ('recycle', 'delete'):
                raise ValueError('未知清理方式')
            if mode == 'delete' and any(g['level'] != SAFE for g in groups):
                raise ValueError('“需确认”的文件群只能移入回收站')
            with LOCK:
                if JOB['running']:
                    return self.reply(409, {'error': '已有清理任务正在进行'})
                JOB = dict(running=True, mode=mode, ids=ids, current=None, total=sum(len(g['files']) for g in groups),
                           processed=0, done_files=0, skipped=0, bytes=0, errors=[], started=time.time())
                threading.Thread(target=run_job, args=(groups, mode), daemon=True).start()
            self.reply(202, {'ok': True})
        except (ValueError, TypeError, RuntimeError, OSError) as exc:
            self.reply(400, {'error': str(exc)})


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    PORT = server.server_address[1]
    ORIGIN = f'http://127.0.0.1:{PORT}'
    state_file = STATE / (hashlib.sha256(str(BASE).encode()).hexdigest()[:12] + '.json')
    state_file.write_text(json.dumps({'pid': os.getpid(), 'host': socket.gethostname(), 'started': time.time(), 'port': PORT, 'url': ORIGIN,
                                      'output': str(BASE), 'script': str(Path(__file__).resolve()), 'python': sys.executable}), encoding='utf-8')
    threading.Thread(target=watch_recycle_bin, daemon=True).start()
    print(ORIGIN, flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
