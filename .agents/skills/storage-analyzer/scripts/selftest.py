"""Exercise isolated snapshots, classification, HTTP guards, deletion and optional recycling."""
import argparse
import importlib.util
import json
import os
import re
import socket
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from common import storage_dir, guarded_path

P = Path(__file__).parent
args = argparse.ArgumentParser()
args.add_argument('--recycle', action='store_true')
args = args.parse_args()
if os.name != 'nt':
    raise SystemExit('Integration checks require Windows')


def run(script, *arguments):
    result = subprocess.run([sys.executable, str(P / script), *map(str, arguments)], capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, (script, result.stdout, result.stderr)
    return result.stdout


with tempfile.TemporaryDirectory(prefix='storage-analyzer-test-') as temporary:
    work = Path(temporary)
    root = work / 'input'; root.mkdir()
    output = work / 'snapshot'
    file = root / '回收验证.txt'; file.write_text('storage analyzer synthetic fixture', encoding='utf-8')
    cache = root / 'cache.bin'; cache.write_bytes(b'x' * 4096)
    st = file.stat(); record = dict(path=str(file), size=st.st_size, mtime=st.st_mtime)
    cst = cache.stat(); cache_record = dict(path=str(cache), size=cst.st_size, mtime=cst.st_mtime)
    assert storage_dir('data', work) == work.resolve()
    previous = os.environ.get('LLM_SKILLS_DATA_DIR')
    os.environ['LLM_SKILLS_DATA_DIR'] = str(work)
    assert storage_dir('data') == work / 'storage-analyzer'
    if previous is None: del os.environ['LLM_SKILLS_DATA_DIR']
    else: os.environ['LLM_SKILLS_DATA_DIR'] = previous
    run('scan.py', '--root', root, '--output', output)
    meta = json.loads((output / 'scan-meta.json').read_text(encoding='utf-8'))
    assert meta['count'] == 2 and meta['root'] == str(root) and meta['drives']
    repeated = subprocess.run([sys.executable, str(P / 'scan.py'), '--root', str(root), '--output', str(output)], capture_output=True)
    assert repeated.returncode != 0
    run('analyze.py', '--output', output)
    run('build_report.py', '--output', output)
    assert (output / 'report.html').is_file()
    assert guarded_path(record, Path.home(), root) == str(file)
    for bad in ({**record, 'size': -1}, {**record, 'path': str(work / 'outside.txt')}, {**record, 'path': str(root / '..' / 'outside.txt')}):
        try:
            guarded_path(bad, Path.home(), root)
            raise AssertionError('Invalid target accepted')
        except (ValueError, FileNotFoundError): pass

    # Synthetic inventory rows exercise classification without touching real caches.
    home, now, old = Path.home(), meta['finished'], meta['finished'] - 10 * 86400
    rows = {
        'pip': (home / 'AppData/Local/pip/cache/http/fixture.bin', now),
        'quark': (home / 'AppData/Roaming/Quark/Cache/videoCache/fixture.bin', now),
        'sw': (home / 'AppData/Local/Google/Chrome/User Data/Default/Service Worker/CacheStorage/a/fixture.bin', now),
        'swdb': (home / 'AppData/Local/Google/Chrome/User Data/Default/Service Worker/Database/fixture.bin', now),
        'temp_old': (home / 'AppData/Local/Temp/setup-x/fixture.bin', old),
        'temp_new': (home / 'AppData/Local/Temp/setup-y/fixture.bin', now),
        'pw_old': (home / 'AppData/Local/ms-playwright/chromium-1100/chrome-win/fixture.bin', now),
        'pw_new': (home / 'AppData/Local/ms-playwright/chromium-1200/chrome-win/fixture.bin', now),
        'mirror': (home / 'AppData/Local/Packages/Fixture_abcdefghijklm/LocalCache/Roaming/FixtureApp/Cache/fixture.bin', now),
        'mirrored': (home / 'AppData/Roaming/FixtureApp/Cache/fixture.bin', now),
        'logs': (home / 'AppData/Roaming/FixtureApp/logs/main.log', old),
    }
    db = sqlite3.connect(output / 'inventory.sqlite')
    db.executemany('INSERT INTO files VALUES (?,?,?,?)', [(str(p), 12 * 2 ** 20, t, 0) for p, t in rows.values()])
    db.commit(); db.close()
    run('analyze.py', '--output', output)
    report = json.loads((output / 'report-data.json').read_text(encoding='utf-8'))
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    grouped = {f['path']: g for g in manifest['groups'] for f in g['files']}
    assert grouped[str(rows['pip'][0])]['level'] == '优先清理'
    assert grouped[str(rows['quark'][0])]['level'] == '需确认'
    assert grouped[str(rows['sw'][0])]['title'] == 'Chrome 缓存'
    assert str(rows['swdb'][0]) not in grouped
    assert str(rows['temp_old'][0]) in grouped and str(rows['temp_new'][0]) not in grouped
    assert grouped[str(rows['pw_old'][0])]['category'] == 'old' and str(rows['pw_new'][0]) not in grouped
    assert str(rows['mirror'][0]) not in grouped and str(rows['mirrored'][0]) in grouped
    assert grouped[str(rows['logs'][0])]['category'] == 'temp'
    assert report['tree']['s'] > 0 and {c['id'] for c in report['categories']} >= {g['category'] for g in report['groups']}
    video = next(g for g in report['groups'] if '夸克' in g['title'])
    decisions = output / 'decisions.json'
    decisions.write_text(json.dumps({video['root']: {'enabled': False}}), encoding='utf-8')
    run('analyze.py', '--output', output, '--decisions', decisions)
    report = json.loads((output / 'report-data.json').read_text(encoding='utf-8'))
    assert next(g for g in report['groups'] if g['id'] == video['id'])['enabled'] is False

    # The server test uses only real files created above.
    manifest = dict(root=str(root), profile=str(Path.home()), groups=[
        dict(id='fixture', title='回收测试', root=str(root), enabled=True, level='需确认', files=[record]),
        dict(id='cache', title='删除测试', root=str(root), enabled=True, level='优先清理', files=[cache_record])])
    (output / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    saved = sys.argv
    sys.argv = ['server.py', '--output', str(output), '--state-dir', str(work / 'state')]
    spec = importlib.util.spec_from_file_location('storage_test_server', P / 'server.py')
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)
    sys.argv = saved
    http = service.ThreadingHTTPServer(('127.0.0.1', 0), service.Handler)
    service.PORT = http.server_address[1]; service.ORIGIN = f'http://127.0.0.1:{service.PORT}'
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()

    def post(route, data, token=None, origin=None):
        headers = {'Content-Type': 'application/json', 'Origin': origin or service.ORIGIN}
        if token: headers['X-Cleanup-Token'] = token
        request = urllib.request.Request(service.ORIGIN + route, data=json.dumps(data).encode(), headers=headers)
        try:
            with urllib.request.urlopen(request) as response: return response.status
        except urllib.error.HTTPError as error: return error.code

    def wait_job():
        deadline = time.monotonic() + 30
        while service.JOB['running'] and time.monotonic() < deadline: time.sleep(.1)
        assert not service.JOB['running'], service.JOB
        return service.JOB

    T = service.TOKEN
    try:
        assert post('/api/shutdown', {'confirmed': True}) == 403
        assert post('/api/shutdown', {'confirmed': True}, T, 'http://untrusted.example') == 403
        assert post('/api/shutdown', {'confirmed': False}, T) == 400
        service.JOB['running'] = True
        assert post('/api/shutdown', {'confirmed': True}, T) == 409
        service.JOB['running'] = False
        service.SYSTEM_JOB['empty-recycle'] = 'running'
        assert post('/api/shutdown', {'confirmed': True}, T) == 409
        service.SYSTEM_JOB.clear()
        assert not service.STOPPING.is_set()
        service.STOPPING.set()
        assert post('/api/clean', {'ids': ['fixture'], 'confirmed': True}, T) == 409
        service.STOPPING.clear()
        assert post('/api/clean', {'ids': ['fixture'], 'confirmed': True}) == 403
        assert post('/api/clean', {'ids': ['fixture'], 'confirmed': True}, T, 'http://untrusted.example') == 403
        assert post('/api/clean', {'ids': ['fixture'], 'confirmed': False}, T) == 400
        assert post('/api/clean', {'ids': ['unknown'], 'confirmed': True}, T) == 400
        assert post('/api/clean', {'ids': ['fixture', 'fixture'], 'confirmed': True}, T) == 400
        assert post('/api/clean', [], T) == 400
        assert post('/api/clean', {'ids': ['fixture'], 'mode': 'delete', 'confirmed': True}, T) == 400
        assert post('/api/system', {'action': 'hibernate-off', 'confirmed': True}, T) == 400
        assert post('/api/open', {'path': str(work / 'outside.txt')}, T) == 400
        service.GROUPS['fixture']['enabled'] = False
        assert post('/api/clean', {'ids': ['fixture'], 'confirmed': True}, T) == 400
        service.GROUPS['fixture']['enabled'] = True
        assert file.exists() and cache.exists()
        assert post('/api/clean', {'ids': ['cache'], 'mode': 'delete', 'confirmed': True}, T) == 202
        job = wait_job()
        assert job['done_files'] == 1 and job['bytes'] == 4096 and not cache.exists(), job
        assert json.loads((output / 'cleaned.json').read_text(encoding='utf-8'))['cache']['mode'] == 'delete'

        # Whole-directory units: only directories made entirely of unchanged manifest files move at once.
        tree = root / 'tree'
        def make(rel, data=b'z' * 512):
            target = tree / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
            s = target.stat(); return dict(path=str(target), size=s.st_size, mtime=s.st_mtime)
        def run_group(group, mode):
            service.GROUPS[group['id']] = group
            service.JOB = dict(running=True, mode=mode, ids=[group['id']], current=None, total=len(group['files']), processed=0,
                               done_files=0, skipped=0, bytes=0, errors=[], started=time.time())
            service.run_job([group], mode)
            return service.JOB
        recs = [make('clean/a/1.bin'), make('clean/b/2.bin'), make('mixed/3.bin'), make('changed/4.bin'), make('locked/5.bin'), make('locked/6.bin')]
        make('mixed/new.bin')
        (tree / 'changed/4.bin').write_bytes(b'changed after scan')
        group = dict(id='tree', title='目录测试', root=str(tree), enabled=True, level='优先清理', files=recs)
        units, loose = service.plan(group, set())
        assert sorted(Path(u).name for u, _, _ in units) == ['clean', 'locked'], units
        assert sorted(Path(r['path']).name for r in loose) == ['3.bin', '4.bin'], loose
        with open(tree / 'locked/5.bin', 'rb'):
            job = run_group(group, 'delete')
        assert job['done_files'] == 4 and job['skipped'] == 2, job
        assert not (tree / 'clean').exists() and not (tree / 'mixed/3.bin').exists() and not (tree / 'locked/6.bin').exists()
        assert (tree / 'mixed/new.bin').exists() and (tree / 'changed/4.bin').exists() and (tree / 'locked/5.bin').exists()
        if args.recycle:
            held, free = make('busy/7.bin', b'held'), make('busy/8.bin', b'free')
            with open(held['path'], 'rb'):
                job = run_group(dict(id='busy', title='占用测试', root=str(tree), enabled=True, level='需确认', files=[held, free]), 'recycle')
            assert job['done_files'] == 1 and job['skipped'] == 1 and Path(held['path']).exists() and not Path(free['path']).exists(), job
            logs = [json.loads(line) for line in (output / 'operations.jsonl').read_text(encoding='utf-8').splitlines()]
            back = next(r['recycle_path'] for e in logs for r in e.get('results', []) if r.get('ok') and r['path'] == free['path'])
            import pythoncom
            from win32com.shell import shell, shellcon
            pythoncom.CoInitialize()
            try:
                op = pythoncom.CoCreateInstance(shell.CLSID_FileOperation, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IFileOperation)
                op.SetOperationFlags(shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_SILENT)
                op.MoveItem(shell.SHCreateItemFromParsingName(back, None, shell.IID_IShellItem), shell.SHCreateItemFromParsingName(str(tree / 'busy'), None, shell.IID_IShellItem), '8.bin', None)
                op.PerformOperations()
            finally: pythoncom.CoUninitialize()
            assert Path(free['path']).read_bytes() == b'free'
        if args.recycle:
            assert post('/api/clean', {'ids': ['fixture'], 'confirmed': True}, T) == 202
            assert wait_job()['done_files'] == 1, service.JOB
            logs = [json.loads(line) for line in (output / 'operations.jsonl').read_text(encoding='utf-8').splitlines()]
            receipt = next(r for entry in logs for r in entry.get('results', []) if r.get('ok') and r['path'] == str(file))
            recycled = Path(receipt['recycle_path'])
            assert recycled.read_text(encoding='utf-8') == 'storage analyzer synthetic fixture'
            import pythoncom
            from win32com.shell import shell, shellcon
            pythoncom.CoInitialize()
            try:
                op = pythoncom.CoCreateInstance(shell.CLSID_FileOperation, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IFileOperation)
                op.SetOperationFlags(shellcon.FOF_NOCONFIRMATION | shellcon.FOF_NOERRORUI | shellcon.FOF_SILENT)
                op.MoveItem(shell.SHCreateItemFromParsingName(str(recycled), None, shell.IID_IShellItem), shell.SHCreateItemFromParsingName(str(root), None, shell.IID_IShellItem), file.name, None)
                op.PerformOperations()
                assert file.read_text(encoding='utf-8') == 'storage analyzer synthetic fixture'
            finally: pythoncom.CoUninitialize()
        assert post('/api/shutdown', {'confirmed': True}, T) == 200
        thread.join(timeout=5)
        assert not thread.is_alive()
        assert service.STOPPING.is_set()
    finally:
        http.shutdown(); http.server_close(); thread.join()

    # Verify the CLI process releases its listener and removes its state record.
    process = subprocess.Popen([sys.executable, '-u', str(P / 'server.py'), '--output', str(output),
                                '--state-dir', str(work / 'state')], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        origin = process.stdout.readline().strip()
        assert origin.startswith('http://127.0.0.1:'), process.stderr.read() if process.poll() is not None else origin
        with urllib.request.urlopen(origin) as response:
            html = response.read().decode('utf-8')
        token = re.search(r"const TOKEN = '([^']+)'", html).group(1)
        request = urllib.request.Request(origin + '/api/shutdown', data=b'{"confirmed":true}',
                                         headers={'Origin': origin, 'X-Cleanup-Token': token, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request) as response:
            assert response.status == 200
        assert process.wait(timeout=5) == 0, process.stderr.read()
        assert not list((work / 'state').glob('*.json'))
        with socket.socket() as probe:
            assert probe.connect_ex(('127.0.0.1', int(origin.rsplit(':', 1)[1]))) != 0
    finally:
        if process.poll() is None:
            process.terminate(); process.wait(timeout=5)
print(json.dumps({'scan': 'passed', 'classification': 'passed', 'override': 'passed', 'path_guards': 'passed', 'http_guards': 'passed',
                  'delete': 'passed', 'directory_units': 'passed', 'shutdown': 'passed', 'recycle_restore': 'passed' if args.recycle else 'not_requested'}))
