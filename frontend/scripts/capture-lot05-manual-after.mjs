import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile, unlink } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD;
if (!/^[a-f0-9]{40}$/.test(PRODUCT_HEAD || '')) {
  throw new Error('Expected exact PR product HEAD');
}
const root = process.cwd();
const out = path.join(root, 'lot05-j10d-manual-after-artifacts');
const htmlPath = path.join(root, 'lot05-j10d-manual-visual.html');
const port = 5199;
const ui = 'http://127.0.0.1:' + port;
const api = 'http://127.0.0.1:8005';
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];
const png = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL/nwAAAABJRU5ErkJggg==',
  'base64',
);
const cors = {
  'access-control-allow-origin': ui,
  'access-control-allow-credentials': 'true',
  'access-control-allow-methods': 'GET,POST,OPTIONS',
  'access-control-allow-headers': 'Authorization,Content-Type,X-Requested-With',
};
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitReady() {
  for (let i = 0; i < 120; i += 1) {
    try {
      const response = await fetch(ui + '/lot05-j10d-manual-visual.html');
      if (response.ok) return;
    } catch {}
    await sleep(250);
  }
  throw new Error('Synthetic visual Vite server not ready');
}
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
await writeFile(htmlPath,
  '<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>LOT05 manual synthetic evidence</title></head><body><div id="root"></div><script type="module" src="/src/lot05-j10d-manual-visual-entry.tsx"></script></body></html>',
);
const vite = path.join(root, 'node_modules', '.bin', 'vite');
const server = spawn(vite, ['--host', '127.0.0.1', '--port', String(port)], {
  cwd: root, env: { ...process.env, BROWSER: 'none', VITE_API_URL: api },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += String(chunk); });
server.stderr.on('data', chunk => { serverLog += String(chunk); });
const report = {
  productHead: PRODUCT_HEAD,
  evidenceType: 'synthetic-browser-mocked-api-NOT-authenticated-clinical-proof',
  beforeAfterSameViewports: true,
  phases: ['before', 'ai-failed', 'manual-draft'],
  captures: [],
  blockedExternalRequests: [],
};
let browser;
let failure;
try {
  await waitReady();
  browser = await chromium.launch({ headless: true });
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const pageErrors = [];
    const serverRequests = [];
    page.on('pageerror', error => pageErrors.push(String(error)));
    page.on('request', request => {
      const url = request.url();
      if (!url.startsWith(ui) && !url.startsWith(api) && !url.startsWith('data:')
          && !url.startsWith('blob:')) {
        report.blockedExternalRequests.push({ viewport: viewport.name, url });
      }
    });
    await page.route(api + '/**', async route => {
      const request = route.request();
      const url = new URL(request.url());
      if (request.method() === 'OPTIONS') {
        await route.fulfill({ status: 204, headers: cors });
      } else if (url.pathname === '/api/ia/upload-radio') {
        serverRequests.push('failed-auto');
        await route.fulfill({
          status: 400, headers: cors, contentType: 'application/json',
          body: JSON.stringify({
            detail: "L'IA n'a détecté aucun point sur cette image. Placement manuel requis.",
          }),
        });
      } else if (url.pathname === '/api/ia/upload-radio-manual') {
        serverRequests.push('explicit-manual');
        await route.fulfill({
          status: 200, headers: cors, contentType: 'application/json',
          body: JSON.stringify({
            status: 'manual_required', analysis_id: 901,
            results: {
              analysis_status: 'MANUAL_DRAFT',
              calibration_status: 'unverified',
              vision_metadata: {
                mode_inference: 'MANUAL_DRAFT',
                warning: 'Placement manuel des 38 repères requis.',
              },
            },
            landmarks: [],
            is_calibrated: false,
            mm_per_pixel: null,
            image_path: 'api/static/uploads/radios/synthetic.png',
          }),
        });
      } else if (url.pathname === '/api/static/uploads/radios/synthetic.png') {
        await route.fulfill({ status: 200, headers: cors, contentType: 'image/png', body: png });
      } else {
        await route.fulfill({ status: 404, headers: cors, contentType: 'application/json',
          body: '{"detail":"Unexpected synthetic endpoint"}' });
      }
    });

    await page.goto(ui + '/lot05-j10d-manual-visual.html', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: 'Importer une radiographie JPEG ou PNG' }).waitFor();
    await page.screenshot({ path: path.join(out, 'before-' + viewport.name + '.png'), fullPage: true });

    await page.locator('input[type="file"]').setInputFiles({
      name: 'synthetic.png', mimeType: 'image/png', buffer: png,
    });
    await page.getByRole('button', { name: /Importer cette radiographie en brouillon manuel/ }).waitFor();
    await page.getByRole('alert').getByText('Placement manuel requis.', { exact: false }).waitFor();
    await page.screenshot({ path: path.join(out, 'ai-failed-' + viewport.name + '.png'), fullPage: true });
    if (serverRequests.join(',') !== 'failed-auto') {
      throw new Error('Auto failure was not the only preceding server operation on ' + viewport.name);
    }

    await page.getByRole('button', { name: /Importer cette radiographie en brouillon manuel/ }).click();
    const manual = page.getByRole('group', { name: 'Traçage céphalométrique manuel' });
    await manual.waitFor();
    await page.getByText('Placement manuel : 0/38 repères', { exact: false }).waitFor();
    const selectors = await page.locator('#cephalo-manual-point option').count();
    const horizontalOverflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > window.innerWidth + 2
    );
    const noInventedMetrics = await page.evaluate(() => {
      const text = document.body.innerText;
      return !text.includes('Auto-calibration réussie') && !text.includes('Diagnostic confirmé');
    });
    await page.screenshot({ path: path.join(out, 'manual-draft-' + viewport.name + '.png'), fullPage: true });

    const valid = selectors === 39 && !horizontalOverflow && noInventedMetrics
      && pageErrors.length === 0 && serverRequests.join(',') === 'failed-auto,explicit-manual';
    report.captures.push({
      viewport: viewport.name, valid, selectors, horizontalOverflow,
      noInventedMetrics, pageErrors, serverRequests,
      synthetic: true,
    });
    if (!valid) throw new Error('Manual browser evidence contract failed: ' + JSON.stringify(report.captures.at(-1)));
    await context.close();
  }
  if (report.blockedExternalRequests.length) throw new Error('Unexpected outside request');
} catch (error) {
  failure = error;
  report.failure = String(error);
  report.viteLogTail = serverLog.slice(-1500);
} finally {
  if (browser) await browser.close();
  server.kill('SIGTERM');
  await unlink(htmlPath).catch(() => {});
  report.valid = !failure && report.captures.length === 3
    && report.captures.every(c => c.valid);
  await writeFile(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
}
if (!report.valid) throw failure || new Error('Invalid manual visual evidence');
console.log('LOT05_MANUAL_SYNTHETIC_AFTER_OK ' + PRODUCT_HEAD);
