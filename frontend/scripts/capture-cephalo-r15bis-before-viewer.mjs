import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'cephalo-r15-after-artifacts');
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
import { CephaloWorkspace } from './features/ortho/CephaloWorkspace';
import { useOrthoStore } from './features/ortho/stores/useOrthoStore';
import './index.css';

const fixture = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(\`
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
    <rect width="1200" height="1600" fill="#e2e8f0"/>
    <path d="M470 220 C720 260 820 520 760 760 C710 960 570 1160 420 1340" fill="none" stroke="#64748b" stroke-width="18" opacity=".38"/>
    <path d="M390 520 C600 450 790 560 820 760 C760 900 620 970 460 940" fill="none" stroke="#94a3b8" stroke-width="12" opacity=".28"/>
  </svg>\`);

useOrthoStore.setState({
  patientId: 915,
  patientName: 'Patient Démo R15',
  analysisId: 9915,
  imageSrc: fixture,
  imgDim: { w: 1200, h: 1600 },
  local: { landmarks: [], version: 1 },
  anglesData: { calibration_status: 'validated', SNA: 82, SNB: 80, ANB: 2, FMA: 25, IMPA: 90 },
  visionMetadata: {},
  isCalibrated: true,
  mmPerPixel: 0.1,
  showCalibration: false,
  calibrationClickPoints: [],
  calibrationDistance: '',
  calibrationStep: 'selecting',
  completedSteps: new Set([1, 2]),
  step: 1,
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/915/cephalo']}>
    <div style={{minHeight:'100vh'}}><CephaloWorkspace patientId={915} patientName="Patient Démo R15" /></div>
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R15bis BEFORE viewer</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r15bis-before-viewer-entry.tsx"></script></body></html>`;
const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try { const response = await fetch(url); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'cephalo-r15bis-before-viewer-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'cephalo-r15bis-before-viewer.html'), htmlSource, 'utf8');

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

async function captureAttempt(viewport, attempt) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1, reducedMotion: 'reduce', locale: 'fr-FR' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  const apiRequests = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });

  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
    if (url.hostname === '127.0.0.1' && url.port === '8005') {
      apiRequests.push(`${request.method()} ${url.pathname}${url.search}`);
      if (request.method() === 'GET' && url.pathname === '/api/patients/915') return route.fulfill(json({ id: 915, nom: 'Démo', prenom: 'R15', age: 34, sexe: 'M' }));
      return route.fulfill(json({ detail: 'Endpoint neutralisé dans le BEFORE viewer R15bis' }, 418));
    }
    if (url.hostname === 'fonts.googleapis.com') return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* offline visual harness */' });
    blockedExternalRequests.push({ viewport: viewport.name, attempt, url: request.url(), method: request.method() });
    return route.abort('blockedbyclient');
  });

  try {
    const response = await page.goto(`${BASE_URL}/cephalo-r15bis-before-viewer.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByRole('heading', { name: 'Céphalométrie' }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText('Édition Active').waitFor({ state: 'visible', timeout: 30000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.waitForTimeout(350);

    const metrics = await page.evaluate(viewportName => {
      const body = document.body;
      const doc = document.documentElement;
      const fullscreenButton = document.querySelector('button[title="Plein écran"], button[title="Quitter plein écran"]');
      let viewer = fullscreenButton?.parentElement ?? null;
      while (viewer && !(viewer.classList.contains('relative') && viewer.classList.contains('flex') && viewer.classList.contains('flex-col'))) viewer = viewer.parentElement;
      const rect = viewer?.getBoundingClientRect() ?? null;
      const styles = getComputedStyle(body);
      const themeTokens = {
        bg: styles.getPropertyValue('--bg-medical-pearl').trim(),
        card: styles.getPropertyValue('--card-bg').trim(),
        text: styles.getPropertyValue('--text-main').trim(),
        primary: styles.getPropertyValue('--primary').trim(),
      };
      return {
        viewport: viewportName,
        innerWidth,
        innerHeight,
        scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
        horizontalDocumentOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
        themeTokensResolved: Object.values(themeTokens).every(Boolean),
        viewerRect: rect ? { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height } : null,
        viewerWidthRatio: rect ? rect.width / innerWidth : 0,
        viewerHeightRatio: rect ? rect.height / innerHeight : 0,
        bodyHeight: body.scrollHeight,
      };
    }, viewport.name);

    const viewerInBounds = Boolean(metrics.viewerRect && metrics.viewerRect.left >= -1 && metrics.viewerRect.right <= viewport.width + 1 && metrics.viewerRect.width > 0 && metrics.viewerRect.height > 0);
    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-step1-viewer-${viewport.name}.png`), fullPage: false });
    return {
      viewport: viewport.name,
      attempt,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      apiRequests,
      ...metrics,
      viewerInBounds,
      valid: response?.status() === 200 && pageErrors.length === 0 && consoleErrors.length === 0 && metrics.themeTokensResolved && !metrics.horizontalDocumentOverflow && viewerInBounds,
    };
  } catch (error) {
    return { viewport: viewport.name, attempt, httpStatus: null, pageErrors: [...pageErrors, error instanceof Error ? error.message : String(error)], consoleErrors, apiRequests, valid: false };
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

try {
  await waitForServer(`${BASE_URL}/cephalo-r15bis-before-viewer.html`);
  for (const viewport of viewports) {
    const attempts = [await captureAttempt(viewport, 1)];
    if (!attempts[0].valid) attempts.push(await captureAttempt(viewport, 2));
    const finalAttempt = attempts.at(-1);
    captures.push({ ...finalAttempt, attempts: attempts.map(({ attempt, valid, httpStatus, pageErrors, consoleErrors }) => ({ attempt, valid, httpStatus, pageErrors, consoleErrors })), recoveredTransientRender: attempts.length === 2 && !attempts[0].valid && attempts[1].valid });
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  if (server.exitCode === null && !server.killed) server.kill('SIGKILL');
  await writeFile(path.join(OUTPUT_DIR, 'viewer-vite.log'), serverLog, 'utf8');
}

const invalid = captures.filter(item => !item.valid);
const report = {
  lot: 'CEPHALO-R15BIS',
  phase: 'BEFORE_VIEWER',
  productHead: PRODUCT_HEAD,
  viewports: viewports.map(item => item.name),
  captures,
  blockedExternalRequests,
  invalidCount: invalid.length,
};
await writeFile(path.join(OUTPUT_DIR, 'viewer-report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (invalid.length > 0 || blockedExternalRequests.length > 0) process.exitCode = 1;
