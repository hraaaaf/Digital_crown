import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'mutuelles-cnss-ui-before-artifacts');
const PORT = 5198;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const doc = {
  id: '9915104',
  name: 'Honoraires_CNSS_Avant.pdf',
  type: 'NOTE',
  date: '15/09/2026',
  url: '/documents/9915104/download',
  file_exists: true,
  clinical_data: {
    payments: [
      { acte: 'Détartrage', dent: '11,21', montant: 500, date: '2026-09-15' },
      { acte: 'Extraction', dent: '36', montant: 700, date: '2026-09-15' },
    ],
  },
  payment_status: 'EN_ATTENTE',
  is_accounted: true,
};

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { PatientDocuments } from './features/patients/PatientDocuments';
import { api } from './services/api';
import './index.css';

const fixture = ${JSON.stringify(doc)};
(api as any).get = async (url: string) => {
  if (url === '/patients/915/documents') return { data: [fixture], status: 200 };
  throw new Error('Unexpected GET in deterministic Mutuelles BEFORE cert: ' + url);
};
(api as any).post = async (url: string) => {
  throw new Error('Unexpected POST in deterministic Mutuelles BEFORE cert: ' + url);
};

document.body.dataset.theme = 'light';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/915']}>
    <Routes><Route path="/patients/:id" element={<PatientDocuments />} /></Routes>
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Mutuelles CNSS UI BEFORE</title><style>html,body,#root{width:100%;min-height:100%;margin:0}body{padding:16px;box-sizing:border-box}</style></head><body><div id="root"></div><script type="module" src="/src/mutuelles-cnss-ui-before-entry.tsx"></script></body></html>`;

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try { const response = await fetch(url); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'mutuelles-cnss-ui-before-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'mutuelles-cnss-ui-before.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += chunk.toString(); });
server.stderr.on('data', chunk => { serverLog += chunk.toString(); });

const captures = [];
const blockedExternalRequests = [];

try {
  await waitForServer(BASE_URL);
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
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
      if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* offline visual harness */' });
      blockedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method() });
      return route.abort('blockedbyclient');
    });

    const response = await page.goto(`${BASE_URL}/mutuelles-cnss-ui-before.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByText(doc.name, { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-card-${viewport.name}.png`), fullPage: false });

    const actionButton = page.getByRole('button', { name: `Actions du document ${doc.name}`, exact: true });
    await actionButton.click();
    await page.locator('[data-document-action-menu]').waitFor({ state: 'visible', timeout: 10000 });
    const hasInsuranceAction = await page.locator('[data-insurance-action="prepare-cnss"]').count() > 0;
    const metrics = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth),
      horizontalOverflow: Math.max(document.body.scrollWidth, document.documentElement.scrollWidth) > innerWidth + 1,
    }));
    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-menu-${viewport.name}.png`), fullPage: false });

    captures.push({
      viewport: viewport.name,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      hasInsuranceAction,
      metrics,
      valid: response?.status() === 200 && !hasInsuranceAction && !metrics.horizontalOverflow && pageErrors.length === 0 && consoleErrors.length === 0,
    });
    await context.close();
    await browser.close();
  }

  const report = {
    certificate: 'MUTUELLES_CNSS_UI_BEFORE_V1',
    phase: 'BEFORE',
    productHead: PRODUCT_HEAD,
    viewports: viewports.map(v => v.name),
    captures,
    blockedExternalRequests,
    invalidCount: captures.filter(c => !c.valid).length,
  };
  await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
  if (report.invalidCount || blockedExternalRequests.length) throw new Error(`Visual BEFORE failed: ${JSON.stringify(report)}`);
} finally {
  server.kill('SIGTERM');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8').catch(() => {});
  await rm(path.join(FRONTEND_DIR, 'src', 'mutuelles-cnss-ui-before-entry.tsx'), { force: true });
  await rm(path.join(FRONTEND_DIR, 'mutuelles-cnss-ui-before.html'), { force: true });
}
