import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const BASELINE_BEFORE = '6eb93c75f91402031ecc2c8fc1f8858372a97b9b';
const BEFORE_ARTIFACT_ID = 9997848118;
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'mobile-superadmin-mob5h-after-artifacts');
const PORT = 5184;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
];

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none', VITE_DC_PREVIEW_DEMO: '1' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', (chunk) => { serverLog += chunk.toString(); });
server.stderr.on('data', (chunk) => { serverLog += chunk.toString(); });

let browser;
const captures = [];
const blockedExternalRequests = [];
const neutralizedExternalRequests = [];
const unexpectedApiRequests = [];

async function screenshotState(page, viewport, state) {
  await page.screenshot({ path: path.join(OUTPUT_DIR, `after-${state}-${viewport.name}.png`), fullPage: false });
}

try {
  await waitForServer(`${BASE_URL}/mobile/superadmin?demo=1`);
  browser = await chromium.launch({ headless: true });

  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
      locale: 'fr-FR',
    });
    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];

    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (url.hostname === '127.0.0.1' && url.port !== String(PORT) && url.pathname.startsWith('/api/')) {
        unexpectedApiRequests.push({ viewport: viewport.name, method: request.method(), url: request.url() });
      }
    });

    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
      if (url.hostname === 'fonts.googleapis.com') {
        neutralizedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method(), mode: 'offline-css-shim' });
        return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* MOB-5H AFTER offline visual harness */' });
      }
      blockedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method() });
      return route.abort('blockedbyclient');
    });

    const response = await page.goto(`${BASE_URL}/mobile/superadmin?demo=1`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.locator('[data-mobile-superadmin]').waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText('MODE DÉMO — SUPERADMIN').waitFor({ state: 'visible', timeout: 30000 });

    const baseMetrics = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      horizontalOverflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > innerWidth + 1,
      hasPreviewIsolationMeta: Boolean(document.querySelector('meta[data-dc-preview-isolation="true"]')),
      sectionButtons: Array.from(document.querySelectorAll('header button')).map(node => (node.textContent || '').trim()).filter(Boolean),
    }));

    await screenshotState(page, viewport, 'overview');

    await page.getByRole('button', { name: 'Clients' }).click();
    await page.getByText('Cabinet Atlas Démo').waitFor({ state: 'visible' });
    await page.getByRole('button', { name: /Cabinet Atlas Démo/ }).click();
    await page.getByRole('dialog', { name: 'Cabinet Atlas Démo' }).waitFor({ state: 'visible' });
    const clientCapabilities = {
      revoke: await page.getByRole('button', { name: /Révoquer licence/i }).isVisible(),
      archive: await page.getByRole('button', { name: /Archiver/i }).isVisible(),
      suspend: await page.getByRole('button', { name: /Suspendre/i }).isVisible(),
      history: await page.getByRole('button', { name: /Historique/i }).isVisible(),
      renewal: await page.getByRole('button', { name: /Relance/i }).isVisible(),
    };
    await screenshotState(page, viewport, 'client-detail');
    await page.getByRole('button', { name: 'Fermer' }).click();

    await page.getByRole('button', { name: 'Essais' }).click();
    await page.getByText('DC-DEMO-42A1-8BC2').waitFor({ state: 'visible' });
    await screenshotState(page, viewport, 'trials');

    await page.getByRole('button', { name: 'Marketplace' }).click();
    await page.getByText('Dental Supply Demo').waitFor({ state: 'visible' });
    const marketplaceCapabilities = {
      suppliers: await page.getByRole('button', { name: 'Fournisseurs' }).isVisible(),
      catalogue: await page.getByRole('button', { name: 'Catalogue' }).isVisible(),
      incidents: await page.getByRole('button', { name: 'Incidents' }).isVisible(),
      audit: await page.getByRole('button', { name: 'Audit' }).isVisible(),
    };
    await screenshotState(page, viewport, 'marketplace');

    await page.getByRole('button', { name: 'Opérations' }).click();
    await page.getByText('CMD-PART-DEMO-7001').waitFor({ state: 'visible' });
    await screenshotState(page, viewport, 'operations');
    await page.getByRole('button', { name: /CMD-PART-DEMO-7001/ }).click();
    await page.getByRole('dialog', { name: 'CMD-PART-DEMO-7001' }).waitFor({ state: 'visible' });
    const operationCapabilities = {
      dispatch: await page.getByRole('button', { name: /Dispatch fournisseur/i }).isVisible(),
      procurement: await page.getByRole('button', { name: /Accuser réception fournisseur/i }).isVisible(),
      invoice: await page.getByRole('button', { name: /Enregistrer facture/i }).isVisible(),
      receipt: await page.getByRole('button', { name: /Enregistrer réception/i }).isVisible(),
    };
    await screenshotState(page, viewport, 'operation-detail');
    await page.getByText('Réception', { exact: true }).scrollIntoViewIfNeeded();
    await screenshotState(page, viewport, 'operation-receipt');

    const finalMetrics = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      horizontalOverflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > innerWidth + 1,
    }));

    captures.push({
      viewport: viewport.name,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      baseMetrics,
      finalMetrics,
      clientCapabilities,
      marketplaceCapabilities,
      operationCapabilities,
    });
    await context.close();
  }
} finally {
  if (browser) await browser.close();
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  if (server.exitCode === null && !server.killed) server.kill('SIGKILL');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const invalid = captures.filter(item =>
  item.httpStatus !== 200 ||
  item.pageErrors.length > 0 ||
  item.consoleErrors.length > 0 ||
  item.baseMetrics.horizontalOverflow ||
  item.finalMetrics.horizontalOverflow ||
  !item.baseMetrics.hasPreviewIsolationMeta ||
  Object.values(item.clientCapabilities).some(value => value !== true) ||
  Object.values(item.marketplaceCapabilities).some(value => value !== true) ||
  Object.values(item.operationCapabilities).some(value => value !== true)
);

const report = {
  lot: 'MOB-5H',
  phase: 'AFTER',
  productHead: PRODUCT_HEAD,
  baselineBefore: BASELINE_BEFORE,
  beforeArtifactId: BEFORE_ARTIFACT_ID,
  viewports: viewports.map(item => item.name),
  captures,
  unexpectedApiRequests,
  neutralizedExternalRequests,
  blockedExternalRequests,
  realExternalEgressAllowed: false,
  invalidCount: invalid.length,
};

await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
if (invalid.length > 0 || unexpectedApiRequests.length > 0 || blockedExternalRequests.length > 0) {
  console.error(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} else {
  console.log(JSON.stringify(report, null, 2));
}
