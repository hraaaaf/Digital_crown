import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.V15_03_5_BASE_URL || 'http://127.0.0.1:5173';
const outDir = path.resolve('../artifacts/v15-03-5-wall-display');
const widths = [390, 430, 768, 1280];
const heightFor = (width) => width <= 430 ? 844 : width <= 768 ? 1024 : 900;
const modes = ['initials', 'full_name', 'number_only'];

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

const identityFor = (mode, initials, fullName) => {
  if (mode === 'number_only') return null;
  return mode === 'full_name' ? fullName : initials;
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

  await page.goto(`${baseUrl}/station`, { waitUntil: 'networkidle' });
  await page.locator('[data-workstation-experience="station"]').waitFor();
  await page.screenshot({ path: path.join(outDir, `before-kiosk-${width}.png`), fullPage: true });

  let wallState = 'waiting';
  let identityMode = 'initials';
  await page.route('**/api/workstation/wall-display*', async route => {
    if (route.request().method() !== 'GET') return route.continue();
    const currentCall = wallState === 'calling'
      ? {
          ticketNumber: 23,
          identityLabel: identityFor(identityMode, 'N. E.', 'Nora El Amrani'),
          expiresAt: new Date(Date.now() + 60_000).toISOString(),
        }
      : null;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        waitingCount: 5,
        entries: [
          { ticketNumber: 12, identityLabel: identityFor(identityMode, 'A. B.', 'Aya Benali') },
          { ticketNumber: 18, identityLabel: identityFor(identityMode, 'S. A.', 'Sara Alami') },
          { ticketNumber: 23, identityLabel: identityFor(identityMode, 'N. E.', 'Nora El Amrani') },
          { ticketNumber: 31, identityLabel: identityFor(identityMode, 'Y. M.', 'Yassine Mansouri') },
        ],
        currentCall,
        callTtlSeconds: 20,
        identityMode,
      }),
    });
  });

  const modeEvidence = [];
  for (const mode of modes) {
    identityMode = mode;
    wallState = 'waiting';
    await page.goto(`${baseUrl}/station/wall`, { waitUntil: 'networkidle' });
    await page.locator('[data-wall-state="waiting"]').waitFor();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    const text = await page.locator('body').innerText();

    if (mode === 'initials' && /Aya Benali|Nora El Amrani|Consultation|diagnostic|téléphone/i.test(text)) {
      throw new Error(`initials wall leaked forbidden text at ${width}px`);
    }
    if (mode === 'number_only' && /A\. B\.|N\. E\.|Aya Benali|Nora El Amrani|Consultation|diagnostic|téléphone/i.test(text)) {
      throw new Error(`number-only wall leaked identity/clinical text at ${width}px`);
    }
    if (mode === 'full_name' && !/Aya Benali/.test(text)) {
      throw new Error(`full-name wall did not render configured identity at ${width}px`);
    }

    await page.screenshot({
      path: path.join(outDir, `after-wall-waiting-${mode}-${width}.png`),
      fullPage: true,
    });

    wallState = 'calling';
    await page.reload({ waitUntil: 'networkidle' });
    await page.locator('[data-wall-state="calling"]').waitFor();
    const callingOverflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    const callingText = await page.locator('body').innerText();
    if (mode === 'number_only' && /N\. E\.|Nora El Amrani/.test(callingText)) {
      throw new Error(`number-only call leaked identity at ${width}px`);
    }
    if (mode === 'full_name' && !/Nora El Amrani/.test(callingText)) {
      throw new Error(`full-name call did not render configured identity at ${width}px`);
    }

    await page.screenshot({
      path: path.join(outDir, `after-wall-calling-${mode}-${width}.png`),
      fullPage: true,
    });

    modeEvidence.push({ mode, waitingOverflow: overflow, callingOverflow });
    if (overflow || callingOverflow) {
      throw new Error(`wall visual overflow at ${width}px/${mode}`);
    }
  }

  evidence.push({ width, height: heightFor(width), modes: modeEvidence, pageErrors: errors });
  if (errors.length) {
    throw new Error(`wall visual gate failed at ${width}px: ${JSON.stringify(evidence.at(-1))}`);
  }
  await context.close();
}

await browser.close();
await fs.writeFile(path.join(outDir, 'evidence.json'), JSON.stringify({
  target: 'Distinct premium public wall with configurable initials/full-name/number-only identity display; no clinical data.',
  beforeReference: 'Existing Station kiosk, intentionally unchanged by 03.5.',
  viewports: evidence,
}, null, 2));
