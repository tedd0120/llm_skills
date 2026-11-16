const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { parseArgs } = require('node:util');
const { Readable } = require('node:stream');
const { execFileSync } = require('node:child_process');
const asar = require('@electron/asar');

const NAME = '360teams-customization';
const BASE_HASH = '7bb8c74d5d80a7aaff62f31982feae619279df3a9c2538bb6d058215cdf6e2d4';
const IMPORTS = {
  [BASE_HASH]: { proxy: false, qwork: true, aiMinutes: true },
  ce85a3f28d4279c81af1ea586a6a9d93050247bb72b4d81c62072ab4259ca71b: { proxy: true, qwork: true, aiMinutes: true },
  b6826b706a2553eff2d6ee29a3435bb99cbf4f2000ecbef03e73cba1e27e545a: { proxy: true, qwork: false, aiMinutes: true },
};
const FILES = {
  qwork: 'dist/modules/qbot/index.js', aiMinutes: 'dist/aiMinutes/AiMinutesController.js',
  startup: 'dist/base/app.js', network: 'dist/tools/NetworkDiagnostics.js',
  package: 'package.json', integrity: 'security/integrity-manifest.json',
  loader: 'dist/teams-customization.cjs', config: 'dist/teams-customization.json',
};
const STARTUP_OLD = "Config[_0x50f0cf(0x130)]&&app[_0x50f0cf(0x118)][_0x50f0cf(0x199)]('no-proxy-server');";
const STARTUP_NEW = "Config[_0x50f0cf(0x130)]&&utils.getStoreValue('network.appMode')!=='system'&&app[_0x50f0cf(0x118)][_0x50f0cf(0x199)]('no-proxy-server');";
const NETWORK_OLD = 'async[_0x503399(0x232)](_0x238746){';
const NETWORK_NEW = NETWORK_OLD + "if(utils.getStoreValue('network.appMode')==='system'){await session.defaultSession.setProxy({mode:'system'});return;}";
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const fileHash = file => hash(fs.readFileSync(file));
const readEntry = (archive, file) => asar.extractFile(archive, path.normalize(file));
const asset = name => fs.readFileSync(path.join(__dirname, '../assets', name));

function directory(kind, explicit) {
  if (explicit) return path.resolve(explicit);
  const environment = process.env[kind === 'state' ? 'LLM_SKILLS_STATE_DIR' : 'LLM_SKILLS_DATA_DIR'];
  if (environment) return path.resolve(environment, NAME);
  for (let parent = __dirname; ; parent = path.dirname(parent)) {
    if (fs.existsSync(path.join(parent, '.git'))) return path.join(parent, kind === 'state' ? '.local' : 'data', NAME);
    if (parent === os.homedir() || parent === path.dirname(parent)) break;
  }
  return path.join(os.homedir(), '.llm-skills', kind === 'state' ? 'local' : 'data', NAME);
}

function entries(header, prefix = '') {
  return Object.entries(header.files).flatMap(([name, info]) => {
    const file = prefix ? `${prefix}/${name}` : name;
    assert(!info.link, `构建含未适配的链接：${file}`);
    return info.files ? [{ file, info }, ...entries(info, file)] : [{ file, info }];
  });
}

function replaceOnce(bytes, before, after) {
  const text = bytes.toString();
  assert.equal(text.split(before).length, 2, '构建补丁语句无法精确匹配');
  return Buffer.from(text.replace(before, after));
}

function featureFiles(readBase, settings) {
  const files = new Map();
  files.set(FILES.qwork, settings.qwork ? readBase(FILES.qwork) : asset('qwork-disabled.cjs'));
  files.set(FILES.aiMinutes, settings.aiMinutes ? readBase(FILES.aiMinutes) : asset('ai-minutes-disabled.cjs'));
  files.set(FILES.startup, settings.proxy ? replaceOnce(readBase(FILES.startup), STARTUP_OLD, STARTUP_NEW) : readBase(FILES.startup));
  files.set(FILES.network, settings.proxy ? replaceOnce(readBase(FILES.network), NETWORK_OLD, NETWORK_NEW) : readBase(FILES.network));
  const disabledRoutes = [...settings.qwork ? [] : ['qbot', 'deepbank'], ...settings.aiMinutes ? [] : ['aiMinutes']];
  if (disabledRoutes.length) {
    const pkg = JSON.parse(readBase(FILES.package));
    assert.equal(pkg.main, 'dist/main.js');
    pkg.main = FILES.loader;
    files.set(FILES.package, Buffer.from(JSON.stringify(pkg, null, 2)));
    files.set(FILES.loader, asset('loader.cjs'));
    files.set(FILES.config, Buffer.from(JSON.stringify({ disabledRoutes })));
  } else files.set(FILES.package, readBase(FILES.package));
  return files;
}

function validateIntegrity(archive) {
  for (const record of JSON.parse(readEntry(archive, FILES.integrity)).files) {
    assert.equal(hash(readEntry(archive, record.path)), record.sha256, `应用清单校验失败：${record.path}`);
  }
}

function checkExecutable(target) {
  const bytes = fs.readFileSync(path.join(path.dirname(target), '../360 Teams.exe'));
  const at = bytes.indexOf(Buffer.from('dL7pKGdnNz796PbbjQWNKmHXBZaB9tsX'));
  assert(at >= 0 && bytes[at + 32] === 1 && bytes[at + 33] >= 5 && bytes[at + 38] === 48, '嵌入式 ASAR 校验已启用或无法识别该可执行文件');
}

function locations(target, explicit) {
  const identity = hash(Buffer.from(path.resolve(target).toLowerCase())).slice(0, 16);
  const root = explicit ? directory('state', explicit) : path.join(directory('state'), identity);
  return { root, state: path.join(root, 'state.json'), base: path.join(root, 'base.asar'), pending: path.join(root, 'pending.json') };
}
function save(file, value) { fs.writeFileSync(file, JSON.stringify(value, null, 2)); }
function load(file) { return JSON.parse(fs.readFileSync(file)); }

function initialize(target, loc, original) {
  assert(!fs.existsSync(loc.state), '该安装已初始化');
  assert(original, 'init 需要 --original-archive 指定已验证的原版程序包');
  assert.equal(fileHash(original), BASE_HASH, '原版程序包与支持构建不符');
  const installedHash = fileHash(target);
  assert(IMPORTS[installedHash], '当前程序包包含未登记的更改，请先适配构建');
  checkExecutable(target);
  validateIntegrity(target);
  fs.mkdirSync(loc.root, { recursive: true });
  fs.copyFileSync(original, loc.base, fs.constants.COPYFILE_EXCL);
  assert.equal(fileHash(loc.base), BASE_HASH);
  const state = { target: path.resolve(target), base_sha256: BASE_HASH, installed_sha256: installedHash, settings: IMPORTS[installedHash] };
  save(loc.state, state);
  return state;
}

function currentState(target, loc) {
  const state = load(loc.state);
  assert.equal(state.target.toLowerCase(), path.resolve(target).toLowerCase(), '状态属于其他安装');
  assert.equal(fileHash(target), state.installed_sha256, '程序包已更新或发生其他更改，停止覆盖');
  assert.equal(fileHash(loc.base), state.base_sha256, '原版备份校验失败');
  return state;
}

async function prepare(target, loc, requested) {
  const state = currentState(target, loc);
  const settings = { ...state.settings, ...requested };
  checkExecutable(target);
  validateIntegrity(target);
  const files = featureFiles(file => readEntry(loc.base, file), settings);
  for (const [file, bytes] of files) if (/\.(js|cjs)$/.test(file)) execFileSync(process.execPath, ['--check'], { input: bytes });
  const integrity = JSON.parse(readEntry(loc.base, FILES.integrity));
  for (const record of integrity.files) {
    record.sha256 = hash(files.get(record.path) || readEntry(target, record.path));
  }
  for (const file of [FILES.loader, FILES.config]) {
    if (files.has(file)) integrity.files.push({ path: file, sha256: hash(files.get(file)) });
  }
  files.set(FILES.integrity, Buffer.from(JSON.stringify(integrity, null, 2)));
  const originalEntries = entries(asar.getRawHeader(target).header);
  const selected = originalEntries.filter(({ file }) => ![FILES.loader, FILES.config].includes(file));
  for (const file of [FILES.loader, FILES.config]) if (files.has(file)) selected.push({ file, info: {} });
  const sourceBody = file => files.get(file) || readEntry(target, file);
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const candidate = path.join(loc.root, stamp, 'app.asar');
  const backup = path.join(loc.root, 'snapshots', state.installed_sha256 + '.asar');
  fs.mkdirSync(path.dirname(backup), { recursive: true });
  if (!fs.existsSync(backup)) fs.copyFileSync(target, backup, fs.constants.COPYFILE_EXCL);
  assert.equal(fileHash(backup), state.installed_sha256);
  await asar.createPackageFromStreams(candidate, selected.map(({ file, info }) => {
    if (info.files) return { path: file, type: 'directory', unpacked: Boolean(info.unpacked) };
    const bytes = sourceBody(file);
    return { path: file, type: 'file', unpacked: Boolean(info.unpacked), stat: { size: bytes.length, mode: info.executable ? 0o100755 : 0o100644 }, streamGenerator: () => Readable.from([bytes]) };
  }));
  asar.uncacheAll();
  assert.deepEqual(entries(asar.getRawHeader(candidate).header).map(row => row.file).sort(), selected.map(row => row.file).sort());
  let verified = 0;
  for (const { file, info } of selected) {
    if (info.files) continue;
    const actual = readEntry(candidate, file);
    assert.equal(hash(actual), hash(sourceBody(file)), `候选包内容不符：${file}`);
    const metadata = asar.statFile(candidate, path.normalize(file));
    assert.equal(Boolean(metadata.unpacked), Boolean(info.unpacked), `unpacked 状态改变：${file}`);
    assert.equal(metadata.integrity.hash, hash(actual), `ASAR 校验失败：${file}`);
    verified++;
  }
  validateIntegrity(candidate);
  assert.equal(fileHash(target), state.installed_sha256, '准备期间程序包发生变化');
  const pending = { target: state.target, before_sha256: state.installed_sha256, before_settings: state.settings, settings, candidate, backup, candidate_sha256: fileHash(candidate), verified_files: verified };
  save(loc.pending, pending);
  return pending;
}

function install(target, loc, restore) {
  const state = currentState(target, loc);
  const pending = load(loc.pending);
  assert.equal(pending.target.toLowerCase(), state.target.toLowerCase());
  const expectedCurrent = restore ? pending.candidate_sha256 : pending.before_sha256;
  const expectedSource = restore ? pending.before_sha256 : pending.candidate_sha256;
  assert.equal(state.installed_sha256, expectedCurrent, '安装状态与待执行操作不符');
  execFileSync('powershell.exe', ['-NoProfile', '-Command', "if (Get-Process -Name '360 Teams' -ErrorAction SilentlyContinue) { exit 1 }"]);
  const source = restore ? pending.backup : pending.candidate;
  assert.equal(fileHash(source), expectedSource, '安装来源校验失败');
  if (!restore) {
    for (const { file, info } of entries(asar.getRawHeader(source).header)) {
      if (info.unpacked && !info.files) assert.equal(hash(readEntry(source, file)), hash(readEntry(target, file)), `原生组件发生变化：${file}`);
    }
  }
  const staging = target + '.customization-install';
  fs.copyFileSync(source, staging, fs.constants.COPYFILE_EXCL);
  assert.equal(fileHash(staging), expectedSource);
  fs.renameSync(staging, target);
  assert.equal(fileHash(target), expectedSource);
  state.installed_sha256 = expectedSource;
  state.settings = restore ? pending.before_settings : pending.settings;
  save(loc.state, state);
  return state;
}

async function main() {
  const { values, positionals } = parseArgs({ allowPositionals: true, options: {
    target: { type: 'string' }, 'state-dir': { type: 'string' }, 'original-archive': { type: 'string' },
    proxy: { type: 'string' }, qwork: { type: 'string' }, 'ai-minutes': { type: 'string' },
    help: { type: 'boolean' },
  } });
  if (values.help) return console.log('customize.cjs init|status|prepare|apply|restore --target <app.asar> [--original-archive <原包>] [--proxy on|off] [--qwork on|off] [--ai-minutes on|off] [--state-dir <目录>]');
  assert(values.target && positionals.length === 1, '需要一个操作和 --target，使用 --help 查看参数');
  const target = path.resolve(values.target);
  const loc = locations(target, values['state-dir']);
  const requested = {};
  for (const [option, key] of [['proxy', 'proxy'], ['qwork', 'qwork'], ['ai-minutes', 'aiMinutes']]) {
    if (values[option] === undefined) continue;
    assert(['on', 'off'].includes(values[option]), `${option} 仅接受 on 或 off`);
    requested[key] = values[option] === 'on';
  }
  const action = positionals[0];
  if (action !== 'prepare') assert.equal(Object.keys(requested).length, 0, '功能选项仅用于 prepare');
  let result;
  if (action === 'init') result = initialize(target, loc, values['original-archive']);
  else if (action === 'status') result = currentState(target, loc);
  else if (action === 'prepare') {
    assert(Object.keys(requested).length, 'prepare 需要指定功能及目标状态');
    result = await prepare(target, loc, requested);
  } else if (action === 'apply' || action === 'restore') result = install(target, loc, action === 'restore');
  else throw new Error('操作无效，使用 --help 查看参数');
  console.log(JSON.stringify({ state_dir: loc.root, ...result }, null, 2));
}

module.exports = { directory, featureFiles, currentState, FILES, STARTUP_OLD, STARTUP_NEW, NETWORK_OLD, NETWORK_NEW };
if (require.main === module) main();
