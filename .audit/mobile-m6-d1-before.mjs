import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m6-d1-before-artifacts';
await fs.rm(output, { recursive: true, force: true });
await fs.mkdir(output, { recursive: true });
const productHead = process.env.PRODUCT_HEAD || 'unknown';
const captures = [];
const server = await createServer({ server: { host: '127.0.0.1', port: 4198, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();

async function capture(width, height) {
  const context = await browser.newContext({ viewport: { width, height }, screen: { width, height }, deviceScaleFactor: 2, hasTouch: true, isMobile: true, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  await page.goto('http://127.0.0.1:4198/mobile-m6-d1-before.html', { waitUntil: 'networkidle' });
  await page.getByText('Agenda du jour', { exact: true }).waitFor({ state: 'visible' });
  const notificationControls = await page.getByRole('button', { name: /notifications?/i }).count();
  const rootMetrics = await page.evaluate(() => ({
    hasHorizontalOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  }));
  await page.screenshot({ path: `${output}/dashboard-notifications-before-${width}x${height}.png`, fullPage: false, animations: 'disabled' });
  captures.push({ width, height, notificationControls, hasHorizontalOverflow: rootMetrics.hasHorizontalOverflow, errors });
  await context.close();
}

try {
  await capture(390, 844);
  await capture(430, 932);
  await capture(768, 1024);
  const report = {
    productHead,
    count: captures.length,
    captures,
    notificationControlAbsentEveryViewport: captures.every(item => item.notificationControls === 0),
    noHorizontalOverflow: captures.every(item => !item.hasHorizontalOverflow),
    noUnexpectedRuntimeErrors: captures.every(item => item.errors.length === 0),
  };
  await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.count !== 3 || !report.notificationControlAbsentEveryViewport || !report.noHorizontalOverflow || !report.noUnexpectedRuntimeErrors) {
    throw new Error('M6-D1 BEFORE evidence gate failed');
  }
} finally {
  await browser.close();
  await server.close();
}
