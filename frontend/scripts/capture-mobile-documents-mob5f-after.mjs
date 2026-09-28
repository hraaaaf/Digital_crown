import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const root = path.resolve(process.cwd(), '..');
const outDir = path.join(root, 'artifacts', 'mobile-documents-mob5f-after');
await fs.mkdir(outDir, { recursive: true });

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
];

const browser = await chromium.launch({ headless: true });
const report = {
  contract: 'patient-cockpit-no-document-authoring',
  viewports: [],
  invalidCount: 0,
  unexpectedApiRequests: [],
  blockedExternalRequests: [],
  realExternalEgressAllowed: false,
};

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const requests = [];

  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('request', (request) => requests.push(request.url()));

  const url = 'http://127.0.0.1:5173/mobile/demo?demo=1&tab=patients';
  const response = await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-mobile-patient-cockpit]');

  const createDocumentVisible = await page.locator('[data-mobile-create-document]').isVisible();
  const clinicalContextVisible = await page.getByText('Contexte clinique', { exact: true }).isVisible();
  const photoVisible = await page.getByRole('button', { name: /Photo clinique/i }).isVisible();
  const scanVisible = await page.getByRole('button', { name: /^Scanner$/i }).isVisible();
  const devisVisible = await page.getByRole('button', { name: /^Devis$/i }).isVisible();
  const honorairesVisible = await page.getByRole('button', { name: /^Honoraires$/i }).isVisible();

  await page.screenshot({
    path: path.join(outDir, `after-cockpit-${viewport.width}x${viewport.height}.png`),
    fullPage: true,
  });

  const metrics = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  const horizontalOverflow = metrics.scrollWidth > metrics.innerWidth;
  const apiRequests = requests.filter((requestUrl) => requestUrl.includes('/api/'));

  const valid = Boolean(response?.ok())
    && !createDocumentVisible
    && clinicalContextVisible
    && photoVisible
    && scanVisible
    && !devisVisible
    && !honorairesVisible
    && !horizontalOverflow
    && pageErrors.length === 0
    && consoleErrors.length === 0
    && apiRequests.length === 0;

  if (!valid) report.invalidCount += 1;
  report.viewports.push({
    viewport,
    httpStatus: response?.status() ?? null,
    createDocumentVisible,
    clinicalContextVisible,
    photoVisible,
    scanVisible,
    devisVisible,
    honorairesVisible,
    horizontalOverflow,
    ...metrics,
    pageErrors,
    consoleErrors,
    apiRequests,
  });

  await context.close();
}

await browser.close();
await fs.writeFile(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
if (report.invalidCount > 0) process.exit(1);
