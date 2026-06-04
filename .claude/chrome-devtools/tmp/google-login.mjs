import { getBrowser, getPage, disconnectBrowser, outputJSON } from '../../skills/vc-chrome-devtools/scripts/lib/browser.js';

async function run() {
  const browser = await getBrowser();
  const page = await getPage(browser);

  const consoleErrors = [];
  const wsConnections = [];

  page.on('console', msg => {
    if (['error', 'warn'].includes(msg.type())) {
      consoleErrors.push({ type: msg.type(), text: msg.text() });
    }
  });

  const client = await page.createCDPSession();
  await client.send('Network.enable');
  client.on('Network.webSocketCreated', ({ url }) => {
    if (url.includes('ghost-insights')) wsConnections.push(url);
  });

  // 1. Login page
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2', timeout: 15000 });
  await page.screenshot({ path: '.claude/chrome-devtools/screenshots/before-google.png' });

  // 2. Click Google button — handle popup
  const [popup] = await Promise.all([
    new Promise(resolve => browser.once('targetcreated', async target => {
      const popupPage = await target.page();
      resolve(popupPage);
    })),
    page.click('button:has-text("Google"), a:has-text("Google"), [class*="google"], [class*="Google"]')
      .catch(() => page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button, a'));
        const g = btns.find(b => b.textContent.includes('Google'));
        if (g) g.click();
      }))
  ]);

  let finalUrl = page.url();

  if (popup) {
    console.error('Google popup opened:', popup.url());
    // Attend que Google redirige (compte déjà connecté = rapide)
    try {
      await popup.waitForNavigation({ timeout: 10000 }).catch(() => {});
      // Si Google redemande un choix de compte, on attend la fermeture auto
      await new Promise(r => setTimeout(r, 5000));
    } catch {}
  }

  // 3. Attendre le redirect vers dashboard
  try {
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 20000 });
  } catch {}

  await new Promise(r => setTimeout(r, 4000));
  finalUrl = page.url();

  await page.screenshot({ path: '.claude/chrome-devtools/screenshots/after-google.png' });

  outputJSON({
    finalUrl,
    loginSuccess: !finalUrl.includes('/login'),
    ghostWsCount: wsConnections.length,
    ghostWsUrls: wsConnections,
    consoleErrors,
  });

  await disconnectBrowser();
}

run().catch(e => {
  console.error('Error:', e.message);
  process.exit(1);
});
