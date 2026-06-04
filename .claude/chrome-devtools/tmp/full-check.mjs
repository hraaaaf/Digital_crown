import { getBrowser, getPage, disconnectBrowser, outputJSON } from '../../skills/vc-chrome-devtools/scripts/lib/browser.js';

const FRONTEND = 'http://localhost:5173';
const EMAIL = 'benmoussa.achraf@gmail.com';
const PASSWORD = 'admin';

async function run() {
  const browser = await getBrowser();
  const page = await getPage(browser);

  const consoleErrors = [];
  const wsConnections = [];
  const network401 = [];

  page.on('console', msg => {
    if (['error','warning','warn'].includes(msg.type())) {
      consoleErrors.push({ type: msg.type(), text: msg.text() });
    }
  });
  page.on('pageerror', err => consoleErrors.push({ type: 'pageerror', text: err.message }));

  // Track WebSocket connections via CDP
  const client = await page.createCDPSession();
  await client.send('Network.enable');
  client.on('Network.webSocketCreated', ({ url }) => wsConnections.push({ event: 'created', url }));
  client.on('Network.webSocketClosed', ({ url }) => wsConnections.push({ event: 'closed', url }));
  client.on('Network.responseReceived', ({ response }) => {
    if (response.status === 401) network401.push(response.url);
  });

  // 1. Login page
  await page.goto(`${FRONTEND}/login`, { waitUntil: 'networkidle2', timeout: 15000 });
  await page.screenshot({ path: '.claude/chrome-devtools/screenshots/login.png' });

  // 2. Fill credentials
  await page.type('input[type="email"]', EMAIL, { delay: 30 });
  await page.type('input[type="password"]', PASSWORD, { delay: 30 });
  await page.click('button[type="submit"]');

  // 3. Wait for dashboard
  try {
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 12000 });
  } catch {}

  const finalUrl = page.url();
  await new Promise(r => setTimeout(r, 3000)); // let WS settle
  await page.screenshot({ path: '.claude/chrome-devtools/screenshots/dashboard.png' });

  outputJSON({
    finalUrl,
    loginSuccess: !finalUrl.includes('/login'),
    consoleErrors,
    wsConnections,
    network401,
    wsCount: wsConnections.filter(w => w.event === 'created').length,
  });

  await disconnectBrowser();
}

run().catch(e => { console.error(e.message); process.exit(1); });
