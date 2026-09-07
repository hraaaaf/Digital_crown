import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.DC_PREVIEW_URL || 'http://127.0.0.1:5173';
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const outDir = process.env.ARTIFACT_DIR || '../artifacts/mobile-waiting-room-mob5i-after';
const targetUrl = `${baseUrl}/mobile/demo?demo=1&tab=waiting-room`;
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

await fs.mkdir(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const results = [];
let invalidCount = 0;

for (const viewport of viewports) {
  const page = await browser.newPage({ viewport });
  const pageErrors = [];
  const consoleErrors = [];

  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

  const response = await page.goto(targetUrl, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-dc-mobile-shell]');
  await page.waitForSelector('[data-mob5i-waiting-room]');

  const metrics = await page.evaluate(() => ({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth }));
  const horizontalOverflow = metrics.scrollWidth > metrics.innerWidth;
  const waitingSurfaceCount = await page.locator('[data-mob5i-waiting-room]').count();
  const waitingCount = Number(await page.locator('[data-mob5i-waiting-count]').getAttribute('data-mob5i-waiting-count'));
  const waitingPatientCount = await page.locator('[data-mob5i-waiting-patient]').count();
  const hasTicket12 = (await page.locator('body').innerText()).includes('#12');
  const hasChairAction = (await page.getByRole('button', { name: /au fauteuil/i }).count()) === 1;

  await page.getByRole('button', { name: 'Plus' }).click();
  const hasWaitingRoomEntry = (await page.locator('[data-mobile-more-item="waiting-room"]').count()) === 1;
  const hasWaitingBadge = (await page.locator('[data-mob5i-waiting-badge]').count()) === 1;
  await page.getByRole('button', { name: 'Fermer Plus' }).click();

  const valid = response?.status() === 200
    && pageErrors.length === 0
    && consoleErrors.length === 0
    && !horizontalOverflow
    && waitingSurfaceCount === 1
    && waitingCount === 1
    && waitingPatientCount === 1
    && hasTicket12
    && hasChairAction
    && hasWaitingRoomEntry
    && hasWaitingBadge;
  if (!valid) invalidCount += 1;

  await page.screenshot({ path: path.join(outDir, `after-${viewport.width}x${viewport.height}.png`), fullPage: false });
  results.push({ viewport, status: response?.status() ?? null, pageErrors, consoleErrors, horizontalOverflow, waitingSurfaceCount, waitingCount, waitingPatientCount, hasTicket12, hasChairAction, hasWaitingRoomEntry, hasWaitingBadge });
  await page.close();
}

await browser.close();
const report = { lot: 'MOB-5I', state: 'AFTER', productHead, targetUrl, viewports: results, invalidCount };
await fs.writeFile(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (invalidCount !== 0) process.exit(1);
