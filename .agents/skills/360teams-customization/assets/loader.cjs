const { app, webContents } = require('electron');
const { disabledRoutes } = require('./teams-customization.json');

const rendererScript = String.raw`(() => {
  const disabledRoutes = DISABLED_ROUTES;
  const router = app.$router;
  const blocked = route => disabledRoutes.some(name =>
    route.path === '/main/apps/' + name || route.path.startsWith('/main/apps/' + name + '/'));
  router.beforeEach((to, from, next) => next(blocked(to) ? '/main/chat' : undefined));
  router.onReady(() => { if (blocked(router.currentRoute)) router.replace('/main/chat'); });
})()`.replace('DISABLED_ROUTES', JSON.stringify(disabledRoutes));

async function customizeRenderer(contents) {
  if (!/^http:\/\/(localhost|127\.0\.0\.1):\d+\//.test(contents.getURL())) return;
  const selectors = disabledRoutes.map(name => name === 'aiMinutes' ? '#navAiMinutes' : '.sidenav-item--' + name).join(',');
  await contents.insertCSS(selectors + ' { display: none !important; }');
  await contents.executeJavaScript(rendererScript);
}
function observe(contents) {
  if (contents.getType() === 'window') contents.on('did-finish-load', () => customizeRenderer(contents));
}
app.on('web-contents-created', (event, contents) => observe(contents));
webContents.getAllWebContents().forEach(observe);
require('./main.js');
