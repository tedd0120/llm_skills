"""Exercise archive preparation and reversible installation using isolated fixtures."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch as mock
import patch
from paths import directory


def fixture():
    bodies = {
        patch.ENTRY: patch.OLD,
        'dist/tools/NetworkDiagnostics.js': b'class N {async[_0x503399(0x232)](_0x238746){}}',
        'untouched.txt': b'preserve these exact bytes',
    }
    integrity = {'files': [{'path': p, 'sha256': patch.sha(b)} for p, b in bodies.items()]}
    bodies['security/integrity-manifest.json'] = json.dumps(integrity).encode()
    header, payload = {'files': {}}, b''
    for path, body in bodies.items():
        parent = header
        parts = path.split('/')
        for part in parts[:-1]:
            parent = parent['files'].setdefault(part, {'files': {}})
        parent['files'][parts[-1]] = {'size': len(body), 'offset': str(len(payload)), 'integrity': {'algorithm': 'SHA256', 'hash': patch.sha(body), 'blockSize': 4194304, 'blocks': [patch.sha(body)]}}
        payload += body
    encoded = json.dumps(header).encode()
    padded = (len(encoded) + 3) // 4 * 4
    return struct.pack('<4I', 4, padded + 8, padded + 4, len(encoded)) + encoded + b'\0' * (padded - len(encoded)) + payload


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        patch.ROOT = root / 'state'
        patch.ROOT.mkdir()
        patch.TARGET = root / 'app' / 'resources' / 'app.asar'
        patch.TARGET.parent.mkdir(parents=True)
        patch.BACKUP = patch.ROOT / 'app.asar.original'
        patch.CANDIDATE = patch.ROOT / 'app.asar.patched'
        patch.MANIFEST = patch.ROOT / 'manifest.json'
        self.original = fixture()
        patch.TARGET.write_bytes(self.original)
        (patch.TARGET.parent.parent / '360 Teams.exe').write_bytes(b'dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX' + b'\x01\x09101100011')

    def tearDown(self):
        self.temp.cleanup()

    def test_roundtrip_preserves_original_and_integrity(self):
        patch.prepare()
        self.assertEqual(patch.TARGET.read_bytes(), self.original)
        header, payload = patch.archive(patch.CANDIDATE.read_bytes())
        self.assertIn(patch.NEW, patch.content(header, payload))
        manifest = json.loads(patch.content(header, payload, 'security/integrity-manifest.json'))
        for row in manifest['files']:
            self.assertEqual(patch.sha(patch.content(header, payload, row['path'])), row['sha256'])
        with mock.object(patch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
            patch.install()
            patch.install()  # idempotent
            patch.install(restore=True)
        self.assertEqual(patch.TARGET.read_bytes(), self.original)
        self.assertEqual(patch.BACKUP.read_bytes(), self.original)

    def test_changed_installation_is_preserved(self):
        patch.prepare()
        patch.TARGET.write_bytes(b'updated client')
        for restore in (False, True):
            with self.assertRaisesRegex(RuntimeError, 'updated or changed'):
                patch.install(restore)
        self.assertEqual(patch.TARGET.read_bytes(), b'updated client')

    def test_running_client_blocks_installation(self):
        patch.prepare()
        with mock.object(patch.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(RuntimeError, 'fully exit'):
                patch.install()
        self.assertEqual(patch.TARGET.read_bytes(), self.original)

    def test_explicit_and_environment_directory_precedence(self):
        with mock.dict('os.environ', {'LLM_SKILLS_STATE_DIR': self.temp.name}):
            self.assertEqual(directory('state'), Path(self.temp.name) / '360teams-proxy-repair')
            explicit = Path(self.temp.name) / 'chosen'
            self.assertEqual(directory('state', explicit), explicit.resolve())


if __name__ == '__main__':
    unittest.main()
