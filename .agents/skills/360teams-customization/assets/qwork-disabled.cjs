const { app, ipcMain } = require('electron');
const { wrapIpcHandleHandler, wrapIpcSyncOnHandler } = require('../../base/ipcEvent/ipcGuard');

const state = Object.freeze({ disabled: true, ready: false, env: '', server: '', ui: '', startupUi: '', provisionedUi: '', surface: '' });
const bridge = Object.freeze({
  disabled: true, shouldInject: false, blocked: true, href: '', qbotUiUrl: '',
  isUiSurface: false, surfaceExists: false, bridgeExists: false, bridgeAbsolute: false,
  appVersion: app.getVersion(), userDataPath: '', qbotDir: '', surfacePath: '', bridgePath: '',
});
let registered = false;
function registerQbotBridgeBootstrapIpc() {
  if (registered) return;
  registered = true;
  ipcMain.on('qbot:get-bridge-bootstrap', wrapIpcSyncOnHandler(
    'qbot:get-bridge-bootstrap', event => { event.returnValue = { ...bridge }; }, bridge,
  ));
  ipcMain.handle('qbot:get-ui-state', wrapIpcHandleHandler('qbot:get-ui-state', () => ({ ...state })));
}
async function bootstrapQbot() {
  registerQbotBridgeBootstrapIpc();
  return { ...state };
}
function initQbotPreloadFiles() { return true; }
module.exports = { bootstrapQbot, initQbotPreloadFiles, refreshQbotPreloadFiles: initQbotPreloadFiles, registerQbotBridgeBootstrapIpc };
