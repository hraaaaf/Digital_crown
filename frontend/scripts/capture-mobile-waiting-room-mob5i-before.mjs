import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const baseUrl = process.env.DC_PREVIEW_URL || 'http://127.0.0.1:5173';
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const outDir = process.env.ARTIFACT_DIR || '../artifacts/mobile-waiting-room-mob5i-before';
const targetUrl = `${baseUrl}/mobile/demo?demo=1&tab=agenda`;
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
  const externalRequests = [];

  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  page.on('request', (request) => {
    const url = request.url();
    if (!url.startsWith(baseUrl) && !url.startsWith('data:') && !url.startsWith('blob:')) externalRequests.push(url);
  });

  const response = await page.goto(targetUrl, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-dc-mobile-shell]');

  const bodyText = await page.locator('body').innerText();
  const waitingSurfaceCount = await page.locator('[data-mob5i-waiting-room]').count();
  const hasWaitingRoomEntry = bodyText.includes('Salle d’attente');
  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  const horizontalOverflow = metrics.scrollWidth > metrics.innerWidth;

  if (
    response?.status() !== 200 ||
    pageErrors.length ||
    consoleErrors.length ||
    horizontalOverflow ||
    waitingSurfaceCount !== 0 ||
    hasWaitingRoomEntry
  ) invalidCount += 1;

  await page.screenshot({
    path: path.join(outDir, `before-${viewport.width}x${viewport.height}.png`),
    fullPage: false,
  });

  results.push({
    viewport,
    status: response?.status() ?? null,
    pageErrors,
    consoleErrors,
    horizontalOverflow,
    scrollWidth: metrics.scrollWidth,
    innerWidth: metrics.innerWidth,
    waitingSurfaceCount,
    hasWaitingRoomEntry,
    externalRequests,
  });
  await page.close();
}

await browser.close();
const report = {
  lot: 'MOB-5I',
  state: 'BEFORE',
  productHead,
  targetUrl,
  viewports: results,
  invalidCount,
  expectedGap: 'Mobile agenda has no dedicated waiting-room surface or navigation entry.',
  backendGap: 'EN_SALLE_ATTENTE is flattened to PLANIFIE and ticket_number is absent from mobile snapshot.',
};
await fs.writeFile(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (invalidCount !== 0) process.exit(1);
