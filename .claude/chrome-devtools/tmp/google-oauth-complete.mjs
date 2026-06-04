import { getBrowser, getPage, disconnectBrowser, outputJSON } from '../../skills/vc-chrome-devtools/scripts/lib/browser.js';

async function run() {
  const browser = await getBrowser();
  const page = await getPage(browser);

  const wsGhost = [];
  const consoleErrors = [];

  page.on('console', msg => {
    if (['error','warn'].includes(msg.type())) consoleErrors.push({ type: msg.type(), text: msg.text() });
  });

  const client = await page.createCDPSession();
  await client.send('Network.enable');
  client.on('Network.webSocketCreated', ({ url }) => {
    if (url.includes('ghost-insights')) wsGhost.push(url);
  });

  // 1. Already on Google login page — type email
  const currentUrl = page.url();
  console.error('Current page:', currentUrl);

  if (currentUrl.includes('accounts.google.com')) {
    // Type email
    await page.waitForSelector('input[type="email"]', { timeout: 8000 });
    await page.click('input[type="email"]');
    await page.type('input[type="email"]', 'lafabriquedapollon@gmail.com', { delay: 50 });
    await page.screenshot({ path: '.claude/chrome-devtools/screenshots/google-email.png' });
    await page.keyboard.press('Enter');
    await new Promise(r => setTimeout(r, 3000));
    await page.screenshot({ path: '.claude/chrome-devtools/screenshots/google-after-email.png' });
  }

  // 2. Wait for redirect back to app
  try {
    await page.waitForFunction(
      () => window.location.hostname === 'localhost',
      { timeout: 30000 }
    );
  } catch {
    console.error('Still not on localhost after 30s');
  }

  await new Promise(r => setTimeout(r, 4000));
  const finalUrl = page.url();
  await page.screenshot({ path: '.claude/chrome-devtools/screenshots/dashboard.png' });

  outputJSON({
    finalUrl,
    loginSuccess: finalUrl.includes('localhost') && !finalUrl.includes('/login'),
    ghostWsCount: wsGhost.length,
    consoleErrors,
  });

  await disconnectBrowser();
}

run().catch(e => { console.error('Error:', e.message); process.exit(1); });
