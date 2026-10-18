"""Group scanned files into cleanup candidates, system actions and a drill-down tree."""
import collections
import hashlib
import heapq
import json
import re
import sqlite3
from pathlib import Path

from common import parser, existing_output

SAFE, REVIEW = '优先清理', '需确认'
OFFLINE = 0x1000 | 0x40000 | 0x400000
GiB, MiB = 2 ** 30, 2 ** 20
MIN_GROUP = 10 * MiB
TREE_MIN = 50 * MiB
TREE_DEPTH = 10

CATEGORIES = [
    dict(id='dev', title='开发工具缓存', desc='包管理器和构建工具的下载缓存。删除后按需重新下载，已安装的项目照常运行。'),
    dict(id='app', title='浏览器与应用缓存', desc='网页、脚本、图形着色器等运行缓存。关闭对应应用后清理，下次打开时自动重建。'),
    dict(id='temp', title='临时文件与日志', desc='安装解压残留、诊断日志、崩溃报告。'),
    dict(id='old', title='旧版本与安装包', desc='已被新版本替代的程序和运行时、更新安装包、下载目录里的旧安装包。'),
    dict(id='media', title='媒体与聊天缓存', desc='视频、音乐、聊天图片的本地缓存。部分内容过期后无法重新下载。'),
]

# Relative-to-profile prefix -> (category, title, level, impact, close)
PREFIX_RULES = [
    ('appdata\\local\\npm-cache', 'dev', 'npm 下载缓存', SAFE, '下次安装依赖时重新下载。', ''),
    ('.npm\\_cacache', 'dev', 'npm 下载缓存', SAFE, '下次安装依赖时重新下载。', ''),
    ('appdata\\local\\pip\\cache', 'dev', 'pip 下载与构建缓存', SAFE, '下次安装 Python 包时重新下载或构建。', ''),
    ('.cache\\pip', 'dev', 'pip 下载缓存', SAFE, '下次安装 Python 包时重新下载。', ''),
    ('appdata\\local\\uv\\cache', 'dev', 'uv 下载与构建缓存', SAFE, '下次安装时重新下载或构建。', 'uv 命令'),
    ('.cache\\uv', 'dev', 'uv 下载缓存', SAFE, '下次安装时重新下载。', 'uv 命令'),
    ('appdata\\local\\pnpm-cache', 'dev', 'pnpm 元数据缓存', SAFE, '下次安装依赖时重新获取。', ''),
    ('appdata\\local\\yarn\\cache', 'dev', 'Yarn 下载缓存', SAFE, '下次安装依赖时重新下载。', ''),
    ('appdata\\local\\yarn\\berry\\cache', 'dev', 'Yarn 下载缓存', SAFE, '下次安装依赖时重新下载。', ''),
    ('appdata\\local\\go-build', 'dev', 'Go 构建缓存', SAFE, '下次编译 Go 项目时重新构建，首次编译变慢。', ''),
    ('appdata\\local\\electron\\cache', 'dev', 'Electron 运行时下载缓存', SAFE, '下次打包 Electron 应用时重新下载。', ''),
    ('appdata\\local\\electron-builder\\cache', 'dev', 'electron-builder 缓存', SAFE, '下次打包时重新下载工具。', ''),
    ('.cargo\\registry\\cache', 'dev', 'Cargo 包下载缓存', SAFE, '下次构建 Rust 项目时重新下载 crate。', 'cargo'),
    ('.cargo\\registry\\src', 'dev', 'Cargo 已解压源码', SAFE, '下次构建时重新解压。', 'cargo'),
    ('appdata\\local\\pypoetry\\cache\\virtualenvs', 'dev', 'Poetry 虚拟环境', REVIEW, '项目需要重新 poetry install；手工装入且未记录的包会丢失。', 'Python'),
    ('appdata\\local\\pypoetry\\cache', 'dev', 'Poetry 下载缓存', SAFE, '下次安装依赖时重新下载。', ''),
    ('.gradle\\caches', 'dev', 'Gradle 缓存', REVIEW, '下次构建重新下载依赖，耗时较长，离线时无法构建。', 'Gradle / IDE'),
    ('.m2\\repository', 'dev', 'Maven 本地仓库', REVIEW, '下次构建重新下载依赖；手工安装到本地仓库的包会丢失。', 'IDE'),
    ('.nuget\\packages', 'dev', 'NuGet 包缓存', REVIEW, '下次还原项目时重新下载。', 'Visual Studio'),
    ('go\\pkg\\mod', 'dev', 'Go 模块缓存', REVIEW, '下次构建重新下载模块。也可以执行 go clean -modcache。', ''),
    ('.cache\\huggingface', 'dev', 'Hugging Face 模型缓存', REVIEW, '模型下次使用时重新下载，体积大、耗时长。', 'Python'),
    ('.conda\\pkgs', 'dev', 'conda 包缓存', REVIEW, '建议用 conda clean --all 清理；已创建的环境不受影响。', 'conda'),
    ('anaconda3\\pkgs', 'dev', 'Anaconda 包缓存', REVIEW, '建议用 conda clean --all 清理；已创建的环境不受影响。', 'conda'),
    ('miniconda3\\pkgs', 'dev', 'Miniconda 包缓存', REVIEW, '建议用 conda clean --all 清理；已创建的环境不受影响。', 'conda'),
    ('.nexe', 'dev', 'nexe 构建缓存', REVIEW, '下次用 nexe 打包时重新下载或编译 Node。', ''),
    ('appdata\\roaming\\quark\\cache', 'media', '夸克视频与页面缓存', REVIEW,
     '先在夸克里把要留的视频另存。缓存视频可能需要重新下载，资源下架后无法找回。', '夸克'),
    ('appdata\\local\\spotify\\data', 'media', 'Spotify 音频缓存', REVIEW,
     '离线下载的歌曲需要重新下载。也可以在 Spotify 设置 → 存储里清理。', 'Spotify'),
    ('appdata\\roaming\\tencent\\xwechat\\log', 'temp', '微信诊断日志', SAFE, '无法再用这些日志排查历史故障。聊天记录不在此目录。', '微信'),
    ('appdata\\local\\crashdumps', 'temp', '应用崩溃转储', SAFE, '失去对应崩溃的诊断材料。', ''),
    ('appdata\\local\\microsoft\\windows\\wer', 'temp', 'Windows 错误报告', SAFE, '失去历史错误报告，系统运行不受影响。', ''),
    ('appdata\\local\\microsoft\\windows\\inetcache', 'app', 'WebView 网页缓存', SAFE, '内嵌网页下次打开时重新加载。', ''),
    ('appdata\\local\\d3dscache', 'app', 'DirectX 着色器缓存', SAFE, '游戏和图形应用下次启动时重建，首次加载略慢。', ''),
    ('appdata\\local\\microsoft\\onedrive\\logs', 'temp', 'OneDrive 日志', SAFE, '失去同步问题的诊断日志。', ''),
]

# Directory-name rules for application caches inside AppData: name -> (category, label, level)
CACHE_NAMES = {
    'cache': ('app', '网页缓存', SAFE), 'code cache': ('app', '脚本缓存', SAFE),
    'gpucache': ('app', '图形缓存', SAFE), 'dawncache': ('app', '图形缓存', SAFE),
    'dawngraphitecache': ('app', '图形缓存', SAFE), 'dawnwebgpucache': ('app', '图形缓存', SAFE),
    'graphitedawncache': ('app', '图形缓存', SAFE), 'grshadercache': ('app', '图形缓存', SAFE),
    'shadercache': ('app', '图形缓存', SAFE), 'gpupersistentcache': ('app', '图形缓存', SAFE),
    'cachestorage': ('app', 'Service Worker 缓存', SAFE), 'scriptcache': ('app', 'Service Worker 缓存', SAFE),
    'cacheddata': ('app', '编译缓存', SAFE), 'cachedextensionvsixs': ('app', '扩展安装包缓存', SAFE),
    'component_crx_cache': ('app', '组件下载缓存', SAFE), 'extensions_crx_cache': ('app', '扩展下载缓存', SAFE),
    'crashpad': ('temp', '崩溃报告', SAFE),
}
CODE_TREES = {'node_modules', 'site-packages', 'vendor', 'src'}
VENDOR_DIRS = {'packages', 'google', 'microsoft', 'tencent', 'programs'}
LOG_EXT = re.compile(r'\.(log|etl|dmp|old)(\.\d+)?$')
INSTALLER_EXT = ('.exe', '.msi', '.msix', '.iso', '.zip', '.7z', '.rar', '.dmg', '.nupkg')

# Version siblings: everything except the newest version under the same parent and family
FAMILY_RULES = [
    (re.compile(r'(?P<parent>appdata\\local\\ms-playwright)\\(?P<child>(?P<family>[a-z_]+)-(?P<ver>\d+))\\'),
     'Playwright 旧版浏览器 · {child}', '确认没有项目固定使用该版本；需要时 playwright install 会重新下载。'),
    (re.compile(r'(?P<parent>\.cache\\puppeteer\\[^\\]+)\\(?P<child>(?P<family>[a-z0-9_]+)-(?P<ver>[\d.]+))\\'),
     'Puppeteer 旧版浏览器 · {child}', '确认没有项目固定使用该版本；需要时会重新下载。'),
    (re.compile(r'(?P<parent>\.codeium\\ws-browser)\\(?P<child>(?P<family>[a-z_]+)-(?P<ver>\d+))\\'),
     'Codeium 旧版浏览器 · {child}', '插件使用最新版本，旧版本仅为历史残留。'),
    (re.compile(r'(?P<parent>appdata\\local\\[^\\]+)\\(?P<child>app-(?P<ver>\d+(?:\.\d+)+))\\'),
     '{app} 旧版本程序 · {child}', '自动更新后保留的旧版本。确认新版本运行正常后清理。'),
    (re.compile(r'(?P<parent>\.local\\share\\claude\\versions)\\(?P<child>(?P<ver>\d+(?:\.\d+)+))(?:\\|$)'),
     'Claude Code 旧版本 · {child}', '保留最新版本，旧版本仅用于回退。'),
    (re.compile(r'(?P<parent>appdata\\local\\microsoft\\onedrive)\\(?P<child>(?P<ver>\d+(?:\.\d+){3}))\\'),
     'OneDrive 旧版本程序 · {child}', '自动更新后保留的旧版本。'),
    (re.compile(r'(?P<parent>[^\\]+\\runtimes\\[^\\]+)\\(?P<child>(?P<ver>\d+(?:\.\d+)+)[^\\]*)\\'),
     '{app} 旧版运行时 · {child}', '工具下载的历史版本运行时，保留最新版本。'),
]


def version_key(text):
    return tuple(int(x) for x in re.findall(r'\d+', text))


APP_NAMES = {
    'chrome': 'Chrome', 'edge': 'Edge', 'code': 'VS Code', 'xwechat': '微信', 'olk': '新版 Outlook', 'msteams': 'Teams',
    'larkshell': '飞书', 'larkinternational': 'Lark', 'terminal server client': '远程桌面', 'wemeet': '腾讯会议',
    'wetype': '微信输入法', 'openai.codex': 'Codex', 'microsoftwindows.client.webexperience': 'Windows 小组件',
    'microsoftwindows.client.cbs': 'Windows 系统界面', 'office': 'Office', 'quark': '夸克',
}


def app_name(nodes, start):
    """Owning application for an AppData path: skip vendor folders and package suffixes."""
    name = nodes[start] if len(nodes) > start else ''
    if name.lower() in VENDOR_DIRS and len(nodes) > start + 1:
        name = nodes[start + 1]
    name = re.sub(r'_[a-z0-9]{13}$', '', name)
    return APP_NAMES.get(name.lower(), name)


def drop_package_mirrors(groups, user):
    """MSIX apps expose LocalCache files again under AppData; keep the AppData copy only."""
    seen = {(r['path'].lower()[len(user):], r['size'], r['mtime']) for g in groups.values() for r in g['files']}
    mirror = re.compile(r'appdata\\local\\packages\\[^\\]+\\localcache\\(roaming|local)\\')
    for group in groups.values():
        kept = []
        for record in group['files']:
            relative = record['path'].lower()[len(user):]
            m = mirror.match(relative)
            if m and ('appdata\\' + relative[m.start(1):], record['size'], record['mtime']) in seen:
                continue
            kept.append(record)
        group['files'] = kept


class Grouper:
    def __init__(self):
        self.groups = {}

    def add(self, root, record, part='', key='', **fields):
        key = (root + key).lower()
        group = self.groups.get(key)
        if group is None:
            group = self.groups[key] = dict(id=hashlib.sha256(key.encode()).hexdigest()[:16], root=root,
                                                     enabled=True, files=[], parts=collections.Counter(), **fields)
        group['files'].append(record)
        group['parts'][part] += record['size']


def classify(path, low, record, age, ctx, grouper, families):
    """Assign one profile file to at most one candidate group."""
    user = ctx['user']
    relative = low[len(user):]
    original = path[len(user):]
    nodes = path.split('\\')
    depth = ctx['profile_depth']
    if relative.startswith('appdata\\local\\temp\\'):
        if age >= ctx['temp_days']:
            grouper.add(path[:len(user)] + 'AppData\\Local\\Temp', record, part=original.split('\\')[3] if relative.count('\\') > 3 else '（根目录文件）',
                        category='temp', title=f'超过 {ctx["temp_days"]} 天的临时文件', level=SAFE,
                        why='安装程序、解压工具和诊断工具留下的临时文件，按修改时间筛选。',
                        impact='仍被占用的文件会自动跳过。', close='安装程序')
        return
    for prefix, category, title, level, impact, close in PREFIX_RULES:
        if relative.startswith(prefix + '\\'):
            root = path[:len(user) + len(prefix)]
            sub = relative[len(prefix) + 1:].split('\\')
            grouper.add(root, record, part=original[len(prefix) + 1:].split('\\')[0] if len(sub) > 1 else '（根目录文件）',
                        category=category, title=title, level=level, why='已识别的应用或工具缓存目录。', impact=impact, close=close)
            return
    for pattern, title, impact in FAMILY_RULES:
        m = pattern.match(relative)
        if m:
            parent = m.group('parent')
            key = (parent, m.groupdict().get('family') or '')
            child_root = path[:len(user) + m.end('child')]
            app = original[:len(parent)].split('\\')[-1]
            families[key].setdefault(child_root, dict(ver=version_key(m.group('ver')), files=[],
                                                      title=title.format(app=app, child=original[m.start('child'):m.end('child')]),
                                                      impact=impact))['files'].append(record)
            return
    if relative.startswith('xwechat_files\\') and '\\cache\\' in relative:
        root = path[:low.index('\\cache\\') + 6]
        grouper.add(root, record, part=low[low.index('\\cache\\') + 7:].split('\\')[0], category='media', title='微信聊天图片与视频缓存',
                    level=REVIEW, why='微信账户 cache 目录中的图片、视频缩略图和临时媒体。',
                    impact='先在微信「设置 → 存储空间」查看。部分过期媒体无法重新下载，确认不需要后再清理。', close='微信')
        return
    if relative.startswith('downloads\\') and low.endswith(INSTALLER_EXT) and age >= 30:
        grouper.add(path[:len(user)] + 'Downloads', record, part=original.split('\\')[1] if relative.count('\\') > 1 else nodes[-1],
                    category='old', title='下载目录里的旧安装包与压缩包', level=REVIEW,
                    why='下载目录中 30 天前的安装程序、镜像和压缩包。',
                    impact='逐个核对：已安装软件的安装包可以删除；压缩包可能是唯一副本。', close='')
        return
    if not relative.startswith('appdata\\'):
        return
    # Updater payloads left by Electron apps and Squirrel packages.
    updater = next((i for i, n in enumerate(nodes) if n.lower().endswith('-updater')), None)
    if updater is not None and low.endswith(INSTALLER_EXT + ('.blockmap',)):
        grouper.add('\\'.join(nodes[:updater + 1]), record, part=nodes[-1], category='old', title=f'{nodes[updater][:-8]} 更新安装包',
                    level=REVIEW, why='应用自动更新下载的安装包。', impact='更新完成后可以清理；正在等待安装的更新需要重新下载。', close=nodes[updater][:-8])
        return
    if relative.startswith('appdata\\local\\quark\\user data\\updates\\'):
        grouper.add(path[:len(user)] + original[:len('appdata\\local\\quark\\user data\\updates')], record, part=nodes[-1], category='old',
                    title='夸克更新安装包', level=REVIEW, why='夸克自动更新下载的安装包。', impact='更新完成后可以清理。', close='夸克')
        return
    m = re.match(r'appdata\\local\\([^\\]+)\\packages\\[^\\]+\.nupkg$', relative)
    if m:
        grouper.add('\\'.join(nodes[:depth + 4]), record, part=nodes[-1], category='old', title=f'{nodes[depth + 2]} 更新包', level=REVIEW,
                    why='Squirrel 更新器保存的完整安装包。', impact='下次更新可能需要下载完整安装包。', close=nodes[depth + 2])
        return
    lower_nodes = low.split('\\')
    if len(nodes) <= depth + 4 or any(n in CODE_TREES for n in lower_nodes):
        return
    app = app_name(nodes, depth + 2)
    sp = ' ' if app[-1:].isascii() else ''
    app_root = '\\'.join(nodes[:depth + 4 if nodes[depth + 2].lower() in VENDOR_DIRS else depth + 3])
    if 'optguideondevicemodel' in lower_nodes:
        i = lower_nodes.index('optguideondevicemodel')
        grouper.add('\\'.join(nodes[:i + 1]), record, part=nodes[i + 1] if len(nodes) > i + 2 else '', category='app', title=f'{app}{sp}本地 AI 模型',
                    level=REVIEW, why='浏览器为本地 AI 功能下载的模型文件。',
                    impact='功能开启时浏览器会重新下载。不需要可在浏览器设置的 AI 功能或 chrome://flags 中关闭。', close=app)
        return
    hit = next((i for i, n in enumerate(lower_nodes) if i >= depth + 3 and n in CACHE_NAMES and i < len(nodes) - 1), None)
    if hit is not None:
        category, label, level = CACHE_NAMES[lower_nodes[hit]]
        part = '\\'.join(nodes[len(app_root.split('\\')):hit + 1])
        title = f'{app}{sp}缓存' if category == 'app' else f'{app}{sp}日志与崩溃报告'
        grouper.add(app_root, record, key='' if category == 'app' else '|logs', part=part or label, category=category, title=title,
                    level=level, why='应用生成的网页、脚本、图形缓存。' if category == 'app' else '应用的诊断日志和崩溃报告。',
                    impact='关闭应用后清理，下次打开时自动重建；首次打开略慢。' if category == 'app' else '失去历史问题的诊断材料。', close=app)
        return
    log_hit = next((i for i, n in enumerate(lower_nodes) if i >= depth + 3 and n in ('logs', 'log') and i < len(nodes) - 1), None)
    if log_hit is not None and LOG_EXT.search(low) and age >= 3:
        grouper.add(app_root, record, key='|logs', part='\\'.join(nodes[len(app_root.split('\\')):log_hit + 1]), category='temp',
                    title=f'{app}{sp}日志与崩溃报告', level=SAFE, why='应用的诊断日志和崩溃报告，只保留 3 天前的文件。',
                    impact='失去历史问题的诊断材料。', close=app)


class Tree:
    """Directory sizes to a fixed depth, pruned to entries worth showing."""

    def __init__(self, root):
        self.root = root.rstrip('\\')
        self.sizes = collections.Counter()
        self.files = []

    def add(self, path, size):
        pos = path.find('\\', len(self.root) + 1)
        depth = 0
        while pos != -1 and depth < TREE_DEPTH:
            self.sizes[path[:pos]] += size
            pos = path.find('\\', pos + 1)
            depth += 1
        if size >= TREE_MIN:
            self.files.append((size, path))

    def build(self, total):
        nodes = {self.root: dict(n=self.root + '\\', p=self.root + '\\', s=total, c=[])}
        for key in sorted((k for k, v in self.sizes.items() if v >= TREE_MIN), key=lambda k: k.count('\\')):
            parent = nodes.get(key[:key.rfind('\\')])
            if parent is not None:
                parent['c'].append(nodes.setdefault(key, dict(n=key[key.rfind('\\') + 1:], p=key, s=self.sizes[key], c=[])))
        for size, path in self.files:
            parent = nodes.get(path[:path.rfind('\\')])
            if parent is not None:
                parent['c'].append(dict(n=path[path.rfind('\\') + 1:], p=path, s=size, f=1))
        for node in nodes.values():
            node['c'].sort(key=lambda x: x['s'], reverse=True)
            del node['c'][40:]
            if not node['c']:
                del node['c']
        return nodes[self.root]


def system_buckets(drive):
    win = drive + '\\windows\\'
    return {
        'recycle': [drive + '\\$recycle.bin\\'],
        'hiberfil': [drive + '\\hiberfil.sys'],
        'pagefile': [drive + '\\pagefile.sys', drive + '\\swapfile.sys'],
        'update': [win + 'softwaredistribution.old', win + 'softwaredistribution\\download\\', drive + '\\$windows.~bt\\',
                   drive + '\\$winreagent\\', drive + '\\windows.old\\', win + 'temp\\', drive + '\\programdata\\microsoft\\windows\\wer\\'],
        'winsxs': [win + 'winsxs\\'],
        'installer': [win + 'installer\\', drive + '\\programdata\\package cache\\'],
        'storeapps': [drive + '\\program files\\windowsapps\\'],
    }


REVIEW_ITEMS = [
    ('xwechat_files', '微信聊天记录与文件', '聊天数据库、收到的文件和图片。数值包含上面单列的微信缓存。',
     '在微信「设置 → 存储空间」按聊天清理大文件，或把存储位置改到其他磁盘。'),
    ('documents\\wechat files', '微信（旧版）聊天记录与文件', '旧版微信的聊天数据和附件。', '确认新版微信已迁移聊天记录后，再决定是否保留。'),
    ('.codex', 'Codex 会话与插件数据', '会话历史数据库、插件和沙箱程序。', '在 Codex 中归档或删除旧会话；数据库文件不要手动删除。'),
    ('documents', '文档', '个人文档和工作产物，体积和时间不能说明是否冗余。', '按项目归档到其他磁盘，或在文档文件夹「属性 → 位置」把整个文件夹移到其他盘。'),
    ('downloads', '下载', '下载的文件。旧安装包已在“旧版本与安装包”里单列。', '按修改时间排序后逐个核对，或把下载文件夹移到其他盘。'),
    ('desktop', '桌面', '桌面文件。', '把大文件移到其他磁盘。'),
    ('videos', '视频', '个人视频。', '移到其他磁盘或网盘。'),
    ('pictures', '图片', '个人图片。', '移到其他磁盘或网盘。'),
    ('.git', '用户目录下的 Git 仓库', '用户主目录本身是一个 Git 仓库，.git 保存了它的全部历史。常见于误在主目录执行 git init。',
     '在主目录执行 git status 确认用途。不需要版本管理时，可在资源管理器中删除 .git 文件夹（只删版本历史，不影响其他文件）。'),
    ('.rustup\\toolchains', 'Rust 工具链', '每个工具链约 0.5–1 GB。', '执行 rustup toolchain list 查看，再用 rustup toolchain uninstall <名称> 卸载不用的版本。'),
    ('appdata\\roaming\\npm\\node_modules', '全局 npm 包', '通过 npm install -g 安装的命令行工具。', '执行 npm ls -g --depth=0 查看，用 npm uninstall -g <包名> 卸载不用的工具。'),
    ('.vscode\\extensions', 'VS Code 扩展', '已安装的编辑器扩展。', '在 VS Code 扩展面板卸载不用的扩展。'),
    ('appdata\\local\\programs', '用户级安装的程序', '安装在用户目录下的应用。', '在「设置 → 应用」卸载不用的程序。'),
]

MOVE_ITEMS = [
    ('appdata\\local\\pip\\cache', 'pip 缓存', 'pip config set global.cache-dir "{d}\\DevCache\\pip"'),
    ('appdata\\local\\npm-cache', 'npm 缓存', 'npm config set cache "{d}\\DevCache\\npm-cache"'),
    ('appdata\\local\\uv\\cache', 'uv 缓存', 'setx UV_CACHE_DIR "{d}\\DevCache\\uv"'),
    ('appdata\\local\\ms-playwright', 'Playwright 浏览器', 'setx PLAYWRIGHT_BROWSERS_PATH "{d}\\DevCache\\ms-playwright"'),
    ('.cache\\puppeteer', 'Puppeteer 浏览器', 'setx PUPPETEER_CACHE_DIR "{d}\\DevCache\\puppeteer"'),
    ('.cache\\huggingface', 'Hugging Face 模型', 'setx HF_HOME "{d}\\DevCache\\huggingface"'),
    ('.gradle', 'Gradle', 'setx GRADLE_USER_HOME "{d}\\DevCache\\gradle"'),
    ('go\\pkg\\mod', 'Go 模块', 'go env -w GOMODCACHE="{d}\\DevCache\\go-mod"'),
    ('xwechat_files', '微信聊天文件', None),
    ('documents', '文档文件夹', None),
    ('downloads', '下载文件夹', None),
]
MOVE_HINTS = {'微信聊天文件': '微信「设置 → 存储空间 → 存储位置」选择其他磁盘，微信会自动迁移。',
              '文档文件夹': '资源管理器中右键「文档」→ 属性 → 位置 → 移动，选择其他磁盘的文件夹。',
              '下载文件夹': '资源管理器中右键「下载」→ 属性 → 位置 → 移动，选择其他磁盘的文件夹。'}


def main():
    p = parser('将扫描结果分组并生成报告数据')
    p.add_argument('--decisions', help='按组根路径指定分类、说明及启用状态的 JSON')
    p.add_argument('--temp-days', type=int, default=2, help='临时文件的最小天数')
    args = p.parse_args()
    base = existing_output(args)
    meta = json.loads((base / 'scan-meta.json').read_text(encoding='utf-8'))
    db = sqlite3.connect(base / 'inventory.sqlite')
    profile = meta['profile']
    ctx = dict(user=profile.lower().rstrip('\\') + '\\', profile_depth=len(Path(profile).parts), temp_days=args.temp_days)
    drive = Path(meta['root']).drive.lower()
    buckets = {k: [p for p in v if p.startswith(meta['root'].lower().rstrip('\\'))] for k, v in system_buckets(drive).items()}
    system_size, system_parts = collections.Counter(), collections.defaultdict(collections.Counter)
    review_size, real_case = collections.Counter(), {}
    grouper, families, tree = Grouper(), collections.defaultdict(dict), Tree(meta['root'])
    scanned_total = 0
    for path, size, mtime, attrs in db.execute('SELECT path,size,mtime,attrs FROM files'):
        scanned_total += size
        tree.add(path, size)
        low = path.lower()
        if low.startswith(ctx['user']):
            relative = low[len(ctx['user']):]
            for prefix, *_ in REVIEW_ITEMS:
                if relative.startswith(prefix + '\\'):
                    review_size[prefix] += size
                    real_case.setdefault(prefix, path[:len(ctx['user']) + len(prefix)])
            for prefix, *_ in MOVE_ITEMS:
                if relative.startswith(prefix + '\\'):
                    review_size['move:' + prefix] += size
                    real_case.setdefault(prefix, path[:len(ctx['user']) + len(prefix)])
            if not attrs & OFFLINE:
                classify(path, low, dict(path=path, size=size, mtime=mtime), (meta['finished'] - mtime) / 86400, ctx, grouper, families)
            continue
        for key, prefixes in buckets.items():
            hit = next((p for p in prefixes if low.startswith(p)), None)
            if hit:
                system_size[key] += size
                system_parts[key][path[:len(hit)].rstrip('\\') if not hit.endswith('softwaredistribution.old') else path[:path.index('\\', len(hit))]] += size

    for (parent, family), children in families.items():
        if len(children) < 2:
            continue
        latest = max(children, key=lambda c: children[c]['ver'])
        for root, child in children.items():
            if root != latest:
                for record in child['files']:
                    grouper.add(root, record, part=record['path'][len(root) + 1:].split('\\')[0] or root.rsplit('\\', 1)[-1],
                                category='old', title=child['title'],
                                level=REVIEW, why=f'同目录下已有更新的版本 {latest.rsplit(chr(92), 1)[-1]}。',
                                impact=child['impact'], close='')

    drop_package_mirrors(grouper.groups, ctx['user'])
    decisions = json.loads(Path(args.decisions).read_text(encoding='utf-8')) if args.decisions else {}
    known = {g['root'] for g in grouper.groups.values()} | {g['id'] for g in grouper.groups.values()}
    unknown = set(decisions) - known
    if unknown:
        raise ValueError('决策路径未匹配本次扫描: ' + str(sorted(unknown)))
    groups = []
    for group in grouper.groups.values():
        override = {**decisions.get(group['root'], {}), **decisions.get(group['id'], {})}
        if set(override) - {'title', 'why', 'impact', 'level', 'enabled', 'category'}:
            raise ValueError('决策只能更新标题、说明、影响、等级、分类和启用状态')
        group.update(override)
        if group['level'] not in (SAFE, REVIEW) or not isinstance(group['enabled'], bool) or group['category'] not in {c['id'] for c in CATEGORIES}:
            raise ValueError('无效的分级、分类或启用状态: ' + group['root'])
        group['bytes'] = sum(x['size'] for x in group['files'])
        group['count'] = len(group['files'])
        group['files'].sort(key=lambda x: x['size'], reverse=True)
        group['parts'] = [[k, v] for k, v in group['parts'].most_common(6)]
        if group['bytes'] >= MIN_GROUP:
            groups.append(group)
    groups.sort(key=lambda g: g['bytes'], reverse=True)
    manifest = dict(groups=groups, root=meta['root'], profile=profile, created=meta['finished'])
    (base / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')

    root_tree = tree.build(scanned_total)
    report = dict(
        root=meta['root'], profile=profile, scanned=meta['count'], scanned_bytes=scanned_total, created=meta['finished'],
        disk=meta['disk'], drives=meta.get('drives', []), errors=len(meta['errors']), reparse=len(meta['skipped_reparse']),
        coverage_errors=meta['errors'][:25], categories=CATEGORIES,
        groups=[{**{k: v for k, v in g.items() if k != 'files'}, 'samples': g['files'][:15]} for g in groups],
        system=system_cards(system_size, system_parts, meta),
        review=review_cards(review_size, real_case),
        moves=move_cards(review_size, real_case, meta),
        largest=[dict(path=p, size=s) for s, p in heapq.nlargest(40, tree.files)],
        tree=root_tree,
    )
    (base / 'report-data.json').write_text(json.dumps(report, ensure_ascii=False), encoding='utf-8')
    db.close()
    print(json.dumps({'groups': len(groups), 'candidate_GiB': round(sum(g['bytes'] for g in groups) / GiB, 2),
                      'priority_GiB': round(sum(g['bytes'] for g in groups if g['level'] == SAFE) / GiB, 2),
                      'system_GiB': round(sum(c['size'] for c in report['system'] if c.get('reclaim')) / GiB, 2)}, ensure_ascii=False))


def system_cards(size, parts, meta):
    """Windows-managed space with the tools that reclaim it."""
    def listing(key):
        return [[k, v] for k, v in parts[key].most_common(8)]
    cards = []
    if size['recycle']:
        cards.append(dict(id='recycle', title='回收站', size=size['recycle'], reclaim=True, live='recycle',
                          explain='移入回收站的文件仍占用磁盘。清空后才真正腾出空间，清空后无法恢复。',
                          actions=[dict(id='open-recycle', label='打开回收站查看'), dict(id='empty-recycle', label='清空回收站', danger=True)]))
    if size['hiberfil']:
        cards.append(dict(id='hiberfil', title='休眠文件 hiberfil.sys', size=size['hiberfil'], reclaim=True,
                          explain='保存休眠时的内存内容，大小约为内存的 40%。笔记本合盖常用“睡眠”，与休眠无关。',
                          impact='关闭休眠：腾出全部空间，同时失去“休眠”和“快速启动”（开机可能慢几秒）。精简模式：只保留快速启动，文件缩小约一半。',
                          actions=[dict(id='hibernate-reduced', label='精简休眠文件', admin=True), dict(id='hibernate-off', label='关闭休眠', admin=True, danger=True)],
                          commands=['powercfg /h /type reduced', 'powercfg /h off']))
    if size['update']:
        cards.append(dict(id='update', title='Windows 更新残留与系统临时文件', size=size['update'], reclaim=True, parts=listing('update'),
                          explain='更新下载缓存、升级残留、旧系统备份和系统临时文件。用系统自带的“磁盘清理”处理最稳妥。',
                          impact='在弹出的磁盘清理中勾选“Windows 更新清理”“临时文件”“以前的 Windows 安装”等项。删除以前的 Windows 安装后无法回退系统版本。',
                          actions=[dict(id='cleanmgr', label='打开磁盘清理（系统文件）', admin=True)]
                          + ([dict(id='remove-sd-old', label='删除旧更新目录', admin=True, danger=True)]
                             if any('softwaredistribution.old' in k.lower() for k in parts['update']) else []),
                          commands=['cleanmgr /d ' + Path(meta['root']).drive]))
    if size['winsxs']:
        cards.append(dict(id='winsxs', title='Windows 组件存储 WinSxS', size=size['winsxs'], reclaim=False,
                          explain='系统组件和更新的备份。大部分文件与系统目录是硬链接，实际占用远小于显示值。只能用系统命令清理。',
                          impact='清理已被替代的旧组件，之后无法卸载已安装的更新。耗时 5–20 分钟。',
                          actions=[dict(id='dism-cleanup', label='运行组件清理', admin=True)],
                          commands=['Dism.exe /Online /Cleanup-Image /AnalyzeComponentStore', 'Dism.exe /Online /Cleanup-Image /StartComponentCleanup']))
    if size['pagefile']:
        others = [d for d in meta.get('drives', []) if d['drive'].lower() != Path(meta['root']).drive.lower() and d['free'] > 30 * GiB]
        cards.append(dict(id='pagefile', title='虚拟内存 pagefile.sys', size=size['pagefile'], reclaim=False,
                          explain='物理内存不够时使用的磁盘空间，由系统自动管理大小。',
                          impact=(f'可以把虚拟内存移到 {others[0]["drive"]}：在“虚拟内存”设置中给 {others[0]["drive"]} 设为“系统管理的大小”，'
                                  f'再把 C: 设为“无分页文件”或较小的固定值，重启后生效。') if others else '保持系统管理，不建议手动删除。',
                          actions=[dict(id='virtual-memory', label='打开性能选项')]))
    if size['storeapps']:
        cards.append(dict(id='storeapps', title='Microsoft Store 应用', size=size['storeapps'], reclaim=False,
                          explain='Store 和系统预装应用的程序包。', impact='在“已安装的应用”里卸载不用的应用。直接删除文件夹会损坏系统。',
                          actions=[dict(id='apps-settings', label='打开已安装的应用')]))
    if size['installer']:
        cards.append(dict(id='installer', title='安装程序维护缓存', size=size['installer'], reclaim=False, parts=listing('installer'),
                          explain='程序修复、升级和卸载需要的安装包。', impact='保留。卸载对应程序后会自动移除。', actions=[]))
    cards.append(dict(id='storage-sense', title='存储感知', size=0, reclaim=False,
                      explain='Windows 自带的自动清理：定期清空临时文件和超过期限的回收站内容。',
                      impact='在设置里开启后按计划运行，可以设置回收站和下载文件夹的保留天数。', actions=[dict(id='storage-settings', label='打开存储设置')]))
    return cards


def review_cards(size, real_case):
    cards = []
    for prefix, title, explain, advice in REVIEW_ITEMS:
        if size[prefix] >= 300 * MiB:
            cards.append(dict(title=title, path=real_case[prefix], size=size[prefix], explain=explain, advice=advice))
    return sorted(cards, key=lambda c: c['size'], reverse=True)


def move_cards(size, real_case, meta):
    others = sorted((d for d in meta.get('drives', []) if d['drive'].lower() != Path(meta['root']).drive.lower() and d['free'] > 30 * GiB),
                    key=lambda d: d['free'], reverse=True)
    if not others:
        return dict(target=None, items=[])
    target = others[0]['drive']
    items = []
    for prefix, title, command in MOVE_ITEMS:
        if size['move:' + prefix] >= 200 * MiB:
            items.append(dict(title=title, path=real_case[prefix], size=size['move:' + prefix],
                              command=command.format(d=target) if command else None, hint=MOVE_HINTS.get(title,
                              '执行命令后新下载写到新位置；旧缓存可以在清理页面删除。')))
    return dict(target=target, free=others[0]['free'], items=sorted(items, key=lambda c: c['size'], reverse=True))


if __name__ == '__main__':
    main()
