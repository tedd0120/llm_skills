"""Read-only Windows proxy evidence. Reports do not include credentials or chat data."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import os
import winreg
from paths import directory


def snapshot():
    command = r"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $p = @(Get-CimInstance Win32_Process | Where-Object Name -eq '360 Teams.exe')
    $ids = @($p | ForEach-Object ProcessId)
    $connections = @(Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue |
        Where-Object { $_.OwningProcess -in $ids } |
        Select-Object RemoteAddress,RemotePort,OwningProcess)
    [pscustomobject]@{
        processes=@($p | Select-Object ProcessId,ExecutablePath,CreationDate)
        connections=$connections
    } | ConvertTo-Json -Depth 4 -Compress
    """
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command], capture_output=True, text=True, encoding='utf8', errors='replace', check=True)
    return json.loads(result.stdout)


def system_proxy():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Internet Settings') as key:
        values = {}
        for name in ('ProxyEnable', 'ProxyServer'):
            try:
                values[name] = winreg.QueryValueEx(key, name)[0]
            except FileNotFoundError:
                values[name] = None
    return values


def probe(url, proxy):
    command = ['curl.exe', '--silent', '--output', 'NUL', '--connect-timeout', '4', '--max-time', '8', '--write-out', '%{http_code}']
    command += ['--noproxy', '*'] if proxy is None else ['--proxy', proxy, '--noproxy', '']
    result = subprocess.run(command + [url], capture_output=True, text=True, timeout=12)
    return {'exit_code': result.returncode, 'http_status': result.stdout.strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir')
    parser.add_argument('--proxy', help='Explicit HTTP/SOCKS URL without credentials')
    parser.add_argument('--probe-url', default='https://sk.360teams.com/nsf.gif')
    args = parser.parse_args()
    if '@' in (args.proxy or ''):
        parser.error('Pass an unauthenticated local proxy endpoint.')
    settings = system_proxy()
    raw = settings.get('ProxyServer') or ''
    # Windows supports either a shared endpoint or per-protocol entries.
    if '=' in raw:
        entries = dict(item.split('=', 1) for item in raw.split(';') if '=' in item)
        endpoint = entries.get('https') or entries.get('http')
    else:
        endpoint = raw
    proxy = args.proxy or (('http://' + endpoint) if endpoint and settings.get('ProxyEnable') else None)
    if '@' in (proxy or ''):
        parser.error('Proxy credentials must not be included in the report.')
    report = {'observed_at': datetime.now().astimezone().isoformat(), 'system_proxy': settings, 'probe_url': args.probe_url, 'effective_probe_proxy': proxy, **snapshot()}
    cfg = Path(os.environ['APPDATA']) / '360Teams' / 'sk-teams-cfg.json'
    if cfg.exists():
        config = json.loads(cfg.read_text(encoding='utf8'))
        report['client'] = {'network_mode': config.get('network', {}).get('mode'), 'app_mode': config.get('network', {}).get('appMode'), 'no_proxy_record': config.get('configInfo', {}).get('NO_PROXY')}
    report['direct_probe'] = probe(args.probe_url, None)
    report['proxy_probe'] = probe(args.probe_url, proxy) if proxy else {'skipped': 'No enabled proxy endpoint detected'}
    report['interpretation'] = 'Point-in-time evidence; correlate the actual client request with Clash and UI before deciding to patch.'
    output = directory('data', args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / ('diagnosis-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print('REPORT=' + str(path))


if __name__ == '__main__':
    main()
