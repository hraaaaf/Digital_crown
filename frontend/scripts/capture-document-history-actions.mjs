import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'document-history-actions-artifacts');
const PORT = 5197;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const doc = {
  id: '9915001',
  name: 'R15_VISUAL_CERT.pdf',
  type: 'LIBRE',
  date: '2026-09-12',
  url: '/documents/9915001/download',
  file_exists: true,
  clinical_data: { title: 'Certification visuelle', content: 'Fixture déterministe' },
  payment_status: 'EN_ATTENTE',
  is_accounted: false,
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
  throw new Error('Unexpected GET in deterministic document-history visual cert: ' + url);
};
(api as any).post = async (url: string) => {
  throw new Error('Unexpected POST in deterministic document-history visual cert: ' + url);
};

document.body.dataset.theme = 'light';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/915']}>
    <Routes><Route path="/patients/:id" element={<PatientDocuments />} /></Routes>
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Document history actions cert</title><style>html,body,#root{width:100%;min-height:100%;margin:0}body{padding:16px;box-sizing:border-box}</style></head><body><div id="root"></div><script type="module" src="/src/document-history-actions-cert-entry.tsx"></script></body></html>`;

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
await writeFile(path.join(FRONTEND_DIR, 'src', 'document-history-actions-cert-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'document-history-actions-cert.html'), htmlSource, 'utf8');

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
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'fr-FR' });
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

    const response = await page.goto(`${BASE_URL}/document-history-actions-cert.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    try {
      await page.getByText(doc.name, { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
    } catch (error) {
      await page.screenshot({ path: path.join(OUTPUT_DIR, `debug-${viewport.name}.png`), fullPage: true });
      await writeFile(path.join(OUTPUT_DIR, `debug-${viewport.name}.txt`), `${error}\n\nBODY:\n${await page.locator('body').innerText()}\n\nPAGE_ERRORS:\n${pageErrors.join('\n')}\n\nCONSOLE_ERRORS:\n${consoleErrors.join('\n')}`, 'utf8');
      throw error;
    }

    const actionButton = page.getByRole('button', { name: `Actions du document ${doc.name}`, exact: true });
    await actionButton.waitFor({ state: 'visible', timeout: 10000 });
    await actionButton.click();
    const edit = page.locator('[data-document-action="edit"]');
    const trash = page.locator('[data-document-action="trash"]');
    await edit.waitFor({ state: 'visible', timeout: 10000 });
    await trash.waitFor({ state: 'visible', timeout: 10000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });

    const metrics = await page.evaluate(() => {
      const body = document.body;
      const html = document.documentElement;
      const edit = document.querySelector('[data-document-action="edit"]')?.getBoundingClientRect();
      const trash = document.querySelector('[data-document-action="trash"]')?.getBoundingClientRect();
      const menu = document.querySelector('[data-document-action-menu]')?.getBoundingClientRect();
      const overlap = edit && trash ? Math.max(0, (edit.y + edit.height) - trash.y) : null;
      return {
        innerWidth,
        scrollWidth: Math.max(body.scrollWidth, html.scrollWidth),
        horizontalOverflow: Math.max(body.scrollWidth, html.scrollWidth) > innerWidth + 1,
        edit: edit ? { x: edit.x, y: edit.y, width: edit.width, height: edit.height } : null,
        trash: trash ? { x: trash.x, y: trash.y, width: trash.width, height: trash.height } : null,
        menu: menu ? { left: menu.left, right: menu.right, top: menu.top, bottom: menu.bottom } : null,
        overlap,
        menuWithinViewport: Boolean(menu && menu.left >= -1 && menu.right <= innerWidth + 1),
      };
    });

    const valid = response?.status() === 200 && !metrics.horizontalOverflow && metrics.overlap === 0 &&
      Boolean(metrics.edit && metrics.edit.height >= 44 && metrics.trash && metrics.trash.height >= 44) &&
      metrics.menuWithinViewport && pageErrors.length === 0 && consoleErrors.length === 0;
    const shot = `document-actions-${viewport.name}.png`;
    await page.screenshot({ path: path.join(OUTPUT_DIR, shot), fullPage: false });
    captures.push({ viewport: viewport.name, httpStatus: response?.status() ?? null, pageErrors, consoleErrors, metrics, shot, valid });
    await context.close();
    await browser.close();
  }

  const report = {
    certificate: 'DOCUMENT_HISTORY_ACTIONS_VISUAL_CERT_V2',
    productHead: PRODUCT_HEAD,
    viewports: viewports.map(v => v.name),
    policy: 'Actual PatientDocuments component, deterministic in-process API fixture, no backend/auth/network dependency, fresh Chromium per viewport.',
    captures,
    blockedExternalRequests,
    invalidCount: captures.filter(c => !c.valid).length,
  };
  await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
  if (report.invalidCount || blockedExternalRequests.length) throw new Error(`Visual certificate failed: ${JSON.stringify(report)}`);
} finally {
  server.kill('SIGTERM');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8').catch(() => {});
  await rm(path.join(FRONTEND_DIR, 'src', 'document-history-actions-cert-entry.tsx'), { force: true });
  await rm(path.join(FRONTEND_DIR, 'document-history-actions-cert.html'), { force: true });
}
