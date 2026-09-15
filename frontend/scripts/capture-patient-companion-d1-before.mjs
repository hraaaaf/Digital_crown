import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'patient-companion-d1-before-artifacts');
const PORT = 5197;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import './index.css';

document.body.dataset.theme = 'light';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/landing']}>
    <LandingPage />
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Patient Companion D1 BEFORE</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/patient-companion-d1-before-entry.tsx"></script></body></html>`;

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'patient-companion-d1-before-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'patient-companion-d1-before.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none', VITE_API_URL: 'http://127.0.0.1:8005' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += chunk.toString(); });
server.stderr.on('data', chunk => { serverLog += chunk.toString(); });

const captures = [];
const blockedExternalRequests = [];

try {
  await waitForServer(`${BASE_URL}/patient-companion-d1-before.html`);
  for (const viewport of viewports) {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
      locale: 'fr-FR',
    });
    const page = await context.newPage();
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
      if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css', body: '/* offline */' });
      blockedExternalRequests.push({ viewport: viewport.name, url: route.request().url(), method: route.request().method() });
      return route.abort('blockedbyclient');
    });

    const response = await page.goto(`${BASE_URL}/patient-companion-d1-before.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByText('DigitalCrown').first().waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText(/Logiciel dentaire nouvelle génération/i).waitFor({ state: 'visible', timeout: 30000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.waitForTimeout(300);

    const metrics = await page.evaluate((viewportName) => {
      const body = document.body;
      const doc = document.documentElement;
      const text = (body.textContent || '').toLowerCase();
      return {
        viewport: viewportName,
        innerWidth,
        scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
        horizontalDocumentOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
        hasBrand: text.includes('digitalcrown'),
        hasCurrentCabinetHero: text.includes('logiciel dentaire nouvelle génération'),
        hasPatientCompanion: text.includes('patient companion'),
        hasPatientSpace: text.includes('espace patient'),
        hasPatientActivation: text.includes('activer mon espace') || text.includes('code d’activation') || text.includes("code d'activation"),
      };
    }, viewport.name);

    // BEFORE certifies the observed D0 state, defects included. Existing responsive
    // overflow or transient marketing-copy state is evidence to preserve in the
    // report, not a reason to falsify the baseline as invalid. D1 validity here is
    // strictly: healthy render + no Patient Companion surface already present.
    const valid = response?.status() === 200
      && pageErrors.length === 0
      && consoleErrors.length === 0
      && !metrics.hasPatientCompanion
      && !metrics.hasPatientSpace
      && !metrics.hasPatientActivation;

    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-public-entry-${viewport.name}.png`), fullPage: false });
    captures.push({ viewport: viewport.name, httpStatus: response?.status() ?? null, pageErrors, consoleErrors, metrics, valid });
    await context.close();
    await browser.close();
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const invalid = captures.filter(item => !item.valid);
const report = {
  lot: 'PATIENT-COMPANION-D1',
  phase: 'BEFORE',
  productHead: PRODUCT_HEAD,
  viewports: viewports.map(item => item.name),
  baseline: 'Exact D0-closed product baseline. Existing visual defects are recorded as BEFORE evidence; only render failure or pre-existing D1 patient surfaces invalidate this certification.',
  captures,
  blockedExternalRequests,
  invalidCount: invalid.length,
};
await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
