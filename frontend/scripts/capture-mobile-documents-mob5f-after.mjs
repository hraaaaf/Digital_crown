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
const report = { viewports: [], invalidCount: 0, unexpectedApiRequests: [], blockedExternalRequests: [], realExternalEgressAllowed: false };

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const requests = [];

  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  page.on('request', (request) => requests.push(request.url()));

  const url = 'http://127.0.0.1:5173/mobile/demo?demo=1&tab=patients';
  const response = await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForSelector('[data-mobile-patient-cockpit]');
  await page.screenshot({ path: path.join(outDir, `after-cockpit-${viewport.width}x${viewport.height}.png`), fullPage: true });

  const createButton = page.locator('[data-mobile-create-document]');
  const createDocumentVisible = await createButton.isVisible();
  await createButton.click();
  await page.waitForSelector('[data-mobile-quick-document]');
  await page.screenshot({ path: path.join(outDir, `after-studio-${viewport.width}x${viewport.height}.png`), fullPage: true });

  const typeLabels = await page.locator('[data-mobile-quick-document] button').allTextContents();
  const expected = ['Ordonnance', 'Certificat', 'Devis', 'Honoraires', 'Document libre'];
  const hasAllTypes = expected.every((label) => typeLabels.some((text) => text.includes(label)));

  await page.getByRole('button', { name: /Certificat/i }).click();
  await page.getByRole('button', { name: /Prévisualiser/i }).click();
  const archiveButton = page.getByRole('button', { name: /Archiver le document/i });
  const archiveConfirmationVisible = await archiveButton.isVisible();
  const previewReadyVisible = await page.getByText(/Aperçu prêt/i).isVisible();
  await page.screenshot({ path: path.join(outDir, `after-preview-${viewport.width}x${viewport.height}.png`), fullPage: true });

  const metrics = await page.evaluate(() => ({ innerWidth: window.innerWidth, scrollWidth: document.documentElement.scrollWidth }));
  const horizontalOverflow = metrics.scrollWidth > metrics.innerWidth;
  const apiRequests = requests.filter((requestUrl) => requestUrl.includes('/api/'));

  const valid = Boolean(response?.ok())
    && createDocumentVisible
    && hasAllTypes
    && archiveConfirmationVisible
    && previewReadyVisible
    && !horizontalOverflow
    && pageErrors.length === 0
    && consoleErrors.length === 0
    && apiRequests.length === 0;
  if (!valid) report.invalidCount += 1;
  report.viewports.push({
    viewport,
    httpStatus: response?.status() ?? null,
    createDocumentVisible,
    hasAllTypes,
    archiveConfirmationVisible,
    previewReadyVisible,
    typeLabels,
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
