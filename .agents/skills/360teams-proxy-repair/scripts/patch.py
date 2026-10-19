"""Local 360Teams 5.6.6 proxy-mode patch. Uses only Python's standard library."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
from paths import directory

ENTRY = "dist/base/app.js"
OLD = b"Config[_0x50f0cf(0x130)]&&app[_0x50f0cf(0x118)][_0x50f0cf(0x199)]('no-proxy-server');"
NEW = b"Config[_0x50f0cf(0x130)]&&utils.getStoreValue('network.appMode')!=='system'&&app[_0x50f0cf(0x118)][_0x50f0cf(0x199)]('no-proxy-server');"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive(data):
    _, header_size, _, json_size = struct.unpack('<4I', data[:16])
    header = json.loads(data[16:16 + json_size])
    return header, data[8 + header_size:]


def entry(header, path=ENTRY):
    item = header
    for part in path.split('/'):
        item = item['files'][part]
    return item


def content(header, payload, path=ENTRY):
    item = entry(header, path)
    start = int(item['offset'])
    return payload[start:start + item['size']]


def prepare():
    data = TARGET.read_bytes()
    if MANIFEST.exists():
        status()
        return
    if BACKUP.exists() and sha(BACKUP.read_bytes()) != sha(data):
        raise RuntimeError('Existing backup does not match the installed original.')
    header, payload = archive(data)
    original = content(header, payload)
    if original.count(OLD) != 1:
        raise RuntimeError('Unsupported client build: expected startup statement was not found exactly once.')
    # Preserve executable security fuses; refuse a build that enforces embedded ASAR integrity.
    exe = (TARGET.parent.parent / '360 Teams.exe').read_bytes()
    marker = b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX'
    pos = exe.find(marker)
    if pos < 0 or exe[pos + 32] != 1 or exe[pos + 33] < 5 or exe[pos + 38] != ord('0'):
        raise RuntimeError('ASAR integrity fuse is enabled or unknown. Executable will not be modified.')
    changed = original.replace(OLD, NEW)
    network_path = 'dist/tools/NetworkDiagnostics.js'
    network_original = content(header, payload, network_path)
    network_old = b'async[_0x503399(0x232)](_0x238746){'
    network_new = network_old + b"if(utils.getStoreValue('network.appMode')==='system'){await session.defaultSession.setProxy({mode:'system'});return;}"
    if network_original.count(network_old) != 1:
        raise RuntimeError('Unsupported network policy implementation.')
    network_changed = network_original.replace(network_old, network_new)
    integrity_path = 'security/integrity-manifest.json'
    integrity = json.loads(content(header, payload, integrity_path))
    changes = {ENTRY: changed, network_path: network_changed}
    for path, body in changes.items():
        records = [record for record in integrity['files'] if record['path'] == path]
        if len(records) != 1 or records[0]['sha256'] != sha(content(header, payload, path)):
            raise RuntimeError('Unexpected application integrity manifest.')
        records[0]['sha256'] = sha(body)
    changes[integrity_path] = json.dumps(integrity, ensure_ascii=False, indent=2).encode()
    new_payload = payload
    for path, body in changes.items():
        item = entry(header, path)
        item['offset'] = str(len(new_payload))
        item['size'] = len(body)
        block = item['integrity']['blockSize']
        item['integrity']['hash'] = sha(body)
        item['integrity']['blocks'] = [sha(body[i:i + block]) for i in range(0, len(body), block)]
        new_payload += body
    encoded = json.dumps(header, ensure_ascii=False, separators=(',', ':')).encode()
    padded = (len(encoded) + 3) // 4 * 4
    new_data = struct.pack('<4I', 4, padded + 8, padded + 4, len(encoded)) + encoded + b'\0' * (padded - len(encoded)) + new_payload
    check_header, check_payload = archive(new_data)
    assert content(check_header, check_payload) == changed
    assert check_payload[:len(payload)] == payload
    old_header, _ = archive(data)
    for record in integrity['files']:
        item = entry(check_header, record['path'])
        body = (TARGET.parent / 'app.asar.unpacked' / record['path']).read_bytes() if item.get('unpacked') else content(check_header, check_payload, record['path'])
        assert sha(body) == record['sha256'], 'Integrity mismatch: ' + record['path']
    for path in changes:
        entry(check_header, path).clear()
        entry(check_header, path).update(entry(old_header, path))
    assert check_header == old_header, 'Unexpected changes to other archive entries'
    # Syntax-check the exact modified entry without executing application code.
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is required for the syntax check.')
    subprocess.run([node, '--check'], input=changed, check=True)
    subprocess.run([node, '--check'], input=network_changed, check=True)
    if not BACKUP.exists():
        BACKUP.write_bytes(data)
    CANDIDATE.write_bytes(new_data)
    assert sha(BACKUP.read_bytes()) == sha(data)
    MANIFEST.write_text(json.dumps({'target': str(TARGET), 'entry': ENTRY, 'original_sha256': sha(data), 'patched_sha256': sha(new_data), 'change': "Honor network.appMode=system when adding no-proxy-server"}, indent=2), encoding='utf8')
    print('Prepared and verified. Original backup saved. Installed application unchanged.')


def status():
    meta = json.loads(MANIFEST.read_text(encoding='utf8'))
    if Path(meta['target']).resolve() != TARGET:
        raise RuntimeError('State belongs to a different installation.')
    current = sha(TARGET.read_bytes())
    state = 'patched' if current == meta['patched_sha256'] else 'original' if current == meta['original_sha256'] else 'different build'
    print('Installed archive:', state)
    return meta, current


def install(restore=False):
    meta, current = status()
    wanted = meta['original_sha256' if restore else 'patched_sha256']
    if current == wanted:
        print('Already in requested state.')
        return
    if current not in (meta['original_sha256'], meta['patched_sha256']):
        raise RuntimeError('Client was updated or changed; refusing to overwrite it.')
    running = subprocess.run(['powershell.exe', '-NoProfile', '-Command', "if (Get-Process -Name '360 Teams' -ErrorAction SilentlyContinue) { exit 1 }"], capture_output=True)
    if running.returncode:
        raise RuntimeError('Please fully exit 360Teams first (Ctrl+Q), then retry.')
    source = BACKUP if restore else CANDIDATE
    if sha(source.read_bytes()) != wanted:
        raise RuntimeError('Backup/candidate checksum mismatch.')
    temp = TARGET.with_name('app.asar.proxy-patch.tmp')
    if temp.exists():
        raise RuntimeError('Temporary install file already exists; inspect it before retrying.')
    shutil.copyfile(source, temp)
    if sha(temp.read_bytes()) != wanted:
        raise RuntimeError('Copied archive checksum mismatch.')
    os.replace(temp, TARGET)
    assert sha(TARGET.read_bytes()) == wanted
    print('Restored original.' if restore else 'Patch applied. Select System default, then start 360Teams normally.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'apply', 'restore', 'status'])
    parser.add_argument('--target', required=True, type=Path, help='Installed app.asar path')
    parser.add_argument('--state-dir', help='Explicit directory for this installation backup')
    args = parser.parse_args()
    action = args.action
    TARGET = args.target.expanduser().resolve()
    identity = sha(str(TARGET).casefold().encode())[:16]
    ROOT = directory('state', args.state_dir) if args.state_dir else directory('state') / identity
    BACKUP = ROOT / 'app.asar.original'
    CANDIDATE = ROOT / 'app.asar.patched'
    MANIFEST = ROOT / 'manifest.json'
    if action == 'prepare':
        ROOT.mkdir(parents=True, exist_ok=True)
    print('STATE_DIR=' + str(ROOT))
    try:
        if action == 'prepare':
            prepare()
        elif action == 'status':
            status()
        else:
            install(action == 'restore')
    except Exception as exc:
        parser.exit(1, f'ERROR: {exc}\n')
