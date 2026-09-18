import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PHASE = process.env.PHASE || 'after';
const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const EXPECTED_OVERJET = process.env.EXPECTED_OVERJET || (PHASE === 'before' ? '+2.6 mm' : '-2.6 mm');
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, `cephalo-v1-04-${PHASE}`);
const PORT = PHASE === 'before' ? 5204 : 5205;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Step3Clinical } from './features/ortho/components/Step3Clinical';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import { computeStep3Data } from './features/ortho/cephaloUtils';
import './index.css';

const landmarks = [
  { id: 'po', x: -10, y: 10 },
  { id: 'or', x: 10, y: 10 },
  { id: 'u1i', x: 1.3, y: 18 },
  { id: 'l1i', x: 3.9, y: 18 },
];
const computed = computeStep3Data(landmarks, 29, 'M', 1.0, null);
const current = useOrthoStore.getState().etape3Data;
useOrthoStore.setState({
  etape3Data: {
    ...current,
    ...computed,
    selectedAnalysis: 'COM',
    age: 29,
    dentaire: { ...current.dentaire, ...(computed.dentaire || {}) },
    osseuse: { ...current.osseuse, ...(computed.osseuse || {}) },
    esthetique: { ...current.esthetique, ...(computed.esthetique || {}) },
  },
});
const P = {
  bgCard:'#ffffff', bgPanel:'#ffffff', bgInput:'#f8fafc',
  border:'#dbe3ee', shadow:'0 10px 28px rgba(15,23,42,.06)',
  accent:'#2563eb', accentWarning:'#d97706',
  text:'#0f172a', textMuted:'#64748b', textDim:'#94a3b8',
};
ReactDOM.createRoot(document.getElementById('root')).render(
  <main className="min-h-screen bg-slate-50 p-3 sm:p-5 lg:p-8">
    <div className="mx-auto max-w-6xl">
      <div className="mb-3 text-xs font-black uppercase tracking-[0.12em] text-slate-500">Céphalométrie · Étape 3 · Cas surplomb inversé</div>
      <Step3Clinical P={P} />
    </div>
  </main>
);
`;
const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>V1-04 signed overjet</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-v1-04-entry.tsx"></script></body></html>`;

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try { const response = await fetch(url); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'cephalo-v1-04-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'cephalo-v1-04.html'), htmlSource, 'utf8');

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
try {
  await waitForServer(`${BASE_URL}/cephalo-v1-04.html`);
  const browser = await chromium.launch({ headless: true });
  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        locale: 'fr-FR',
        reducedMotion: 'reduce',
      });
      const page = await context.newPage();
      const pageErrors = [];
      const consoleErrors = [];
      page.on('pageerror', error => pageErrors.push(error.message));
      page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
        if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* offline visual harness */' });
        if (url.hostname === 'fonts.gstatic.com') return route.fulfill({ status: 204, body: '' });
        return route.abort('blockedbyclient');
      });
      const response = await page.goto(`${BASE_URL}/cephalo-v1-04.html`, { waitUntil: 'networkidle', timeout: 30000 });
      await page.getByText('Surplomb mesuré', { exact: true }).waitFor({ state: 'visible', timeout: 15000 });
      const label = page.getByText('Surplomb mesuré', { exact: true }).first();
      const rowText = await label.evaluate(el => el.parentElement?.textContent || '');
      if (!rowText.includes(EXPECTED_OVERJET)) throw new Error(`Expected ${EXPECTED_OVERJET}, got ${rowText}`);
      const layout = await page.evaluate(() => ({
        clientWidth: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      if (layout.scrollWidth > layout.clientWidth + 1) throw new Error(`Horizontal overflow at ${viewport.name}`);
      await page.screenshot({
        path: path.join(OUTPUT_DIR, `${PHASE}-step3-${viewport.name}.png`),
        fullPage: true,
        animations: 'disabled',
      });
      captures.push({ viewport: viewport.name, rowText, layout, pageErrors, consoleErrors, httpStatus: response?.status() ?? null, valid: pageErrors.length === 0 && consoleErrors.length === 0 });
      await context.close();
    }
  } finally {
    await browser.close();
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  await rm(path.join(FRONTEND_DIR, 'src', 'cephalo-v1-04-entry.tsx'), { force: true });
  await rm(path.join(FRONTEND_DIR, 'cephalo-v1-04.html'), { force: true });
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}
const report = {
  lot: 'V1-04',
  phase: PHASE.toUpperCase(),
  productHead: PRODUCT_HEAD,
  expectedOverjet: EXPECTED_OVERJET,
  fixture: 'clinical_orientation_reference',
  viewports: viewports.map(v => v.name),
  captures,
};
await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (captures.some(c => !c.valid)) process.exitCode = 1;
