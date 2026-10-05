import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.V15_03_5_BASE_URL || 'http://127.0.0.1:5173';
const outDir = path.resolve('../artifacts/v15-03-5-wall-display');
const widths = [390, 430, 768, 1280];
const heightFor = (width) => width <= 430 ? 844 : width <= 768 ? 1024 : 900;

await fs.mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const evidence = [];

const bootstrap = {
  workstationId: 'visual-wall-station',
  displayName: 'Écran salle d’attente',
  defaultExperience: 'station',
  stationLocked: true,
  stationEscapeAuthorized: false,
  stationEscapeExpiresAt: null,
  enrollmentRequired: false,
  authenticated: true,
  pinConfigured: true,
  canManage: false,
  canConfigurePin: false,
};

for (const width of widths) {
  const context = await browser.newContext({ viewport: { width, height: heightFor(width) } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.route('**/api/workstation/bootstrap*', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(bootstrap),
  }));

  // BEFORE reference: existing public-facing Station kiosk. This surface is
  // unchanged by 03.5 and establishes the visual separation baseline.
  await page.goto(`${baseUrl}/station`, { waitUntil: 'networkidle' });
  await page.locator('[data-workstation-experience="station"]').waitFor();
  await page.screenshot({ path: path.join(outDir, `before-kiosk-${width}.png`), fullPage: true });

  let wallState = 'waiting';
  await page.route('**/api/workstation/wall-display*', async route => {
    if (route.request().method() !== 'GET') return route.continue();
    const currentCall = wallState === 'calling'
      ? {
          ticketNumber: 23,
          identityLabel: 'N. E.',
          expiresAt: new Date(Date.now() + 60_000).toISOString(),
        }
      : null;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        waitingCount: 5,
        entries: [
          { ticketNumber: 12, identityLabel: 'A. B.' },
          { ticketNumber: 18, identityLabel: 'S. A.' },
          { ticketNumber: 23, identityLabel: 'N. E.' },
          { ticketNumber: 31, identityLabel: 'Y. M.' },
        ],
        currentCall,
        callTtlSeconds: 20,
        identityMode: 'initials',
      }),
    });
  });

  await page.goto(`${baseUrl}/station/wall`, { waitUntil: 'networkidle' });
  await page.locator('[data-wall-state="waiting"]').waitFor();
  const waitingOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  const waitingText = await page.locator('body').innerText();
  if (/BENALI|EL AMRANI|Consultation|diagnostic|téléphone/i.test(waitingText)) {
    throw new Error(`public wall leaked forbidden text at ${width}px`);
  }
  await page.screenshot({ path: path.join(outDir, `after-wall-waiting-${width}.png`), fullPage: true });

  wallState = 'calling';
  await page.reload({ waitUntil: 'networkidle' });
  await page.locator('[data-wall-state="calling"]').waitFor();
  const callingOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  await page.screenshot({ path: path.join(outDir, `after-wall-calling-${width}.png`), fullPage: true });

  evidence.push({ width, height: heightFor(width), waitingOverflow, callingOverflow, pageErrors: errors });
  if (waitingOverflow || callingOverflow || errors.length) {
    throw new Error(`wall visual gate failed at ${width}px: ${JSON.stringify(evidence.at(-1))}`);
  }
  await context.close();
}

await browser.close();
await fs.writeFile(path.join(outDir, 'evidence.json'), JSON.stringify({
  target: 'Distinct premium public wall with cabinet-configurable identity display; default initials; bounded staff call; no clinical data.',
  beforeReference: 'Existing Station kiosk, intentionally unchanged by 03.5.',
  viewports: evidence,
}, null, 2));
