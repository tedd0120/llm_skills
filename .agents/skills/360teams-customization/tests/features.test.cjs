const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { EventEmitter } = require('node:events');
const { featureFiles, currentState, directory, FILES, STARTUP_OLD, STARTUP_NEW, NETWORK_OLD, NETWORK_NEW } = require('../scripts/customize.cjs');

const base = new Map([
  [FILES.qwork, Buffer.from('original-qwork')], [FILES.aiMinutes, Buffer.from('original-ai-minutes')],
  [FILES.startup, Buffer.from(STARTUP_OLD)], [FILES.network, Buffer.from(NETWORK_OLD)],
  [FILES.package, Buffer.from(JSON.stringify({ main: 'dist/main.js' }))],
]);

test('八种功能组合独立生成，重新启用恢复原文件', () => {
  for (const proxy of [true, false]) for (const qwork of [true, false]) for (const aiMinutes of [true, false]) {
    const files = featureFiles(file => base.get(file), { proxy, qwork, aiMinutes });
    assert.equal(files.get(FILES.startup).toString(), proxy ? STARTUP_NEW : STARTUP_OLD);
    assert.equal(files.get(FILES.network).toString(), proxy ? NETWORK_NEW : NETWORK_OLD);
    if (qwork) assert.equal(files.get(FILES.qwork).toString(), 'original-qwork');
    else assert(files.get(FILES.qwork).toString().includes('shouldInject: false'));
    if (aiMinutes) assert.equal(files.get(FILES.aiMinutes).toString(), 'original-ai-minutes');
    else assert(files.get(FILES.aiMinutes).toString().includes('40301'));
    assert.equal(files.has(FILES.loader), !qwork || !aiMinutes);
    if (files.has(FILES.config)) assert.deepEqual(JSON.parse(files.get(FILES.config)).disabledRoutes,
      [...qwork ? [] : ['qbot', 'deepbank'], ...aiMinutes ? [] : ['aiMinutes']]);
    else assert.deepEqual(files.get(FILES.package), base.get(FILES.package));
  }
});

test('AI 灵记控制器无需依赖即可返回闲置和停用状态', async () => {
  const controller = require('../assets/ai-minutes-disabled.cjs');
  assert.equal(controller.getStatus().state, 'idle');
  assert.equal(controller.getStatus().disabled, true);
  for (const operation of ['start', 'resume', 'pause', 'stop']) {
    assert.equal((await controller.record({ operation })).bizCode, 40301);
  }
  assert.equal((await controller.audioConfig({ operation: 'set' })).disabled, true);
  assert.equal(controller.publishAudioEvent({ event: 'ready' }).disabled, true);
});

test('QWork 保留受保护的状态和同步桥接接口', async () => {
  const handlers = new Map();
  const context = { module: { exports: {} }, require(name) {
    if (name === 'electron') return { app: { getVersion: () => '5.6.6' }, ipcMain: {
      on: (key, fn) => handlers.set(key, fn), handle: (key, fn) => handlers.set(key, fn),
    } };
    assert.equal(name, '../../base/ipcEvent/ipcGuard');
    return { wrapIpcHandleHandler: (key, fn) => fn, wrapIpcSyncOnHandler: (key, fn) => fn };
  } };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/qwork-disabled.cjs'), 'utf8'), context);
  assert.equal((await context.module.exports.bootstrapQbot()).disabled, true);
  context.module.exports.registerQbotBridgeBootstrapIpc();
  assert.equal(handlers.size, 2);
  const event = {};
  handlers.get('qbot:get-bridge-bootstrap')(event);
  assert.equal(event.returnValue.shouldInject, false);
  assert.equal(handlers.get('qbot:get-ui-state')().ready, false);
});

test('界面启动器按开关隐藏入口并阻止对应路由', async () => {
  for (const disabledRoutes of [['aiMinutes'], ['qbot', 'deepbank'], ['qbot', 'deepbank', 'aiMinutes']]) {
    const app = new EventEmitter();
    let loaded = false, css, script;
    const contents = new EventEmitter();
    contents.getType = () => 'window';
    contents.getURL = () => 'http://localhost:33013/#/main/chat';
    contents.insertCSS = async value => { css = value; };
    contents.executeJavaScript = async value => { script = value; };
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../assets/loader.cjs'), 'utf8'), { require(name) {
      if (name === 'electron') return { app, webContents: { getAllWebContents: () => [] } };
      if (name === './teams-customization.json') return { disabledRoutes };
      assert.equal(name, './main.js'); loaded = true;
    } });
    assert(loaded);
    app.emit('web-contents-created', {}, contents);
    await contents.listeners('did-finish-load')[0]();
    for (const name of disabledRoutes) assert(css.includes(name === 'aiMinutes' ? '#navAiMinutes' : '.sidenav-item--' + name));
    let guard, redirected;
    const router = { currentRoute: { path: '/main/apps/' + disabledRoutes[0] },
      beforeEach: fn => { guard = fn; }, onReady: fn => fn(), replace: to => { redirected = to; } };
    vm.runInNewContext(script, { app: { $router: router } });
    assert.equal(redirected, '/main/chat');
    for (const name of ['qbot', 'deepbank', 'aiMinutes', 'approval']) {
      guard({ path: '/main/apps/' + name }, {}, to => assert.equal(to, disabledRoutes.includes(name) ? '/main/chat' : undefined));
    }
    script = undefined;
    contents.getURL = () => 'https://approval.sk.360shuke.com/hub';
    await contents.listeners('did-finish-load')[0]();
    assert.equal(script, undefined);
  }
});

test('显式目录优先，环境目录按 skill 分隔', () => {
  const original = process.env.LLM_SKILLS_STATE_DIR;
  process.env.LLM_SKILLS_STATE_DIR = path.resolve(__dirname, '../../../../.local/test-state');
  assert.equal(directory('state'), path.join(process.env.LLM_SKILLS_STATE_DIR, '360teams-customization'));
  assert.equal(directory('state', __dirname), __dirname);
  if (original === undefined) delete process.env.LLM_SKILLS_STATE_DIR;
  else process.env.LLM_SKILLS_STATE_DIR = original;
});

test('客户端更新或原包备份变化时停止处理', () => {
  const testRoot = path.resolve(__dirname, '../../../../.local/360teams-customization/tests');
  fs.mkdirSync(testRoot, { recursive: true });
  const fixture = fs.mkdtempSync(path.join(testRoot, 'state-'));
  const target = path.join(fixture, 'installed.asar');
  const loc = { state: path.join(fixture, 'state.json'), base: path.join(fixture, 'base.asar') };
  const digest = value => crypto.createHash('sha256').update(value).digest('hex');
  fs.writeFileSync(target, 'installed');
  fs.writeFileSync(loc.base, 'base');
  fs.writeFileSync(loc.state, JSON.stringify({ target, installed_sha256: digest('installed'), base_sha256: digest('base') }));
  assert.equal(currentState(target, loc).installed_sha256, digest('installed'));
  fs.writeFileSync(target, 'updated');
  assert.throws(() => currentState(target, loc), /程序包已更新/);
  fs.writeFileSync(target, 'installed');
  fs.writeFileSync(loc.base, 'changed');
  assert.throws(() => currentState(target, loc), /原版备份校验失败/);
  assert(fixture.startsWith(testRoot + path.sep));
  fs.rmSync(fixture, { recursive: true });
});
