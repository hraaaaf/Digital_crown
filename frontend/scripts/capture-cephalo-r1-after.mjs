import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'cephalo-r1-after-artifacts');
const PORT = 5188;
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

document.body.dataset.theme = 'dark';
const fixture = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(\`
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600" viewBox="0 0 1200 1600">
    <defs><radialGradient id="g"><stop offset="0" stop-color="#334155"/><stop offset="1" stop-color="#020617"/></radialGradient></defs>
    <rect width="1200" height="1600" fill="url(#g)"/>
    <path d="M470 220 C720 260 820 520 760 760 C710 960 570 1160 420 1340" fill="none" stroke="#94a3b8" stroke-width="18" opacity=".38"/>
    <path d="M390 520 C600 450 790 560 820 760 C760 900 620 970 460 940" fill="none" stroke="#cbd5e1" stroke-width="12" opacity=".28"/>
    <circle cx="680" cy="470" r="105" fill="none" stroke="#e2e8f0" stroke-width="10" opacity=".24"/>
  </svg>\`);

useOrthoStore.setState({
  patientId: 901,
  patientName: 'Patient Démo R1',
  analysisId: 9901,
  imageSrc: fixture,
  imgDim: { w: 1200, h: 1600 },
  local: { landmarks: [], version: 1 },
  anglesData: {
    calibration_status: 'candidate_unverified',
    calibration_candidate: {
      status: 'CANDIDATE_UNVERIFIED',
      detector_method: 'CLASSICAL_RULER_GEOMETRY_V1',
      axis_x_px: 40,
      tick_positions_y_px: [10, 35, 60, 85, 110],
      median_tick_spacing_px: 25,
      mm_per_pixel: null,
      distance_mm: null,
      clinician_validated: false,
    },
  },
  visionMetadata: {},
  isCalibrated: false,
  mmPerPixel: null,
  showCalibration: false,
  calibrationClickPoints: [],
  calibrationDistance: '',
  calibrationStep: 'selecting',
  completedSteps: new Set([1]),
  step: 1,
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/patients/901/cephalo']}>
    <div style={{height:'100vh'}}><CephaloWorkspace patientId={901} patientName="Patient Démo R1" /></div>
  </MemoryRouter>,
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Cephalo R1 AFTER</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/cephalo-r1-after-entry.tsx"></script></body></html>`;

function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

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

function isInvalidMetrics(metrics) {
  return (
    metrics.horizontalDocumentOverflow ||
    metrics.assistantClipped ||
    metrics.headerClipped ||
    !metrics.hasCandidateLabel ||
    !metrics.hasAutoAction ||
    !metrics.hasManualFallback ||
    !metrics.hasWorkspaceHeading
  );
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'cephalo-r1-after-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'cephalo-r1-after.html'), htmlSource, 'utf8');

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

async function captureViewport(viewport, attempt) {
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
  const requests = [];

  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });

  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
    if (url.hostname === '127.0.0.1' && url.port === '8005') {
      const record = `${request.method()} ${url.pathname}${url.search}`;
      requests.push(record);
      if (request.method() === 'GET' && url.pathname === '/api/patients/901') {
        return route.fulfill(json({ id: 901, nom: 'Démo', prenom: 'R1', age: 34, sexe: 'M' }));
      }
      return route.fulfill(json({ detail: 'Endpoint neutralisé dans le AFTER visuel' }, 418));
    }
    if (url.hostname === 'fonts.googleapis.com') {
      return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* offline visual harness */' });
    }
    blockedExternalRequests.push({ viewport: viewport.name, attempt, url: request.url(), method: request.method() });
    return route.abort('blockedbyclient');
  });

  try {
    const response = await page.goto(`${BASE_URL}/cephalo-r1-after.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByRole('heading', { name: 'Studio Céphalométrique' }).waitFor({ state: 'visible', timeout: 30000 });
    const provenanceButton = page.locator('button[title="État de calibration et provenance"]').first();
    await provenanceButton.waitFor({ state: 'visible', timeout: 30000 });
    await provenanceButton.evaluate(button => button.click());
    await page.getByRole('button', { name: /Vérifier automatiquement/i }).waitFor({ state: 'visible', timeout: 30000 });
    await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
    await page.waitForTimeout(300);

    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      const body = document.body;
      const text = (body.textContent || '').toLowerCase();
      const assistantButton = Array.from(document.querySelectorAll('button')).find(node => node.textContent?.toLowerCase().includes('vérifier automatiquement'));
      const assistant = assistantButton?.closest('div.absolute');
      const assistantRect = assistant?.getBoundingClientRect();
      const topHeader = Array.from(document.querySelectorAll('h2')).find(node => node.textContent?.includes('Studio Céphalométrique'))?.parentElement?.parentElement;
      const headerRect = topHeader?.getBoundingClientRect();
      return {
        innerWidth,
        scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
        horizontalDocumentOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
        assistantRect: assistantRect ? { left: assistantRect.left, right: assistantRect.right, top: assistantRect.top, bottom: assistantRect.bottom, width: assistantRect.width } : null,
        assistantClipped: Boolean(assistantRect && (assistantRect.left < -1 || assistantRect.right > innerWidth + 1 || assistantRect.top < -1 || assistantRect.bottom > innerHeight + 1)),
        headerRect: headerRect ? { left: headerRect.left, right: headerRect.right, width: headerRect.width } : null,
        headerClipped: Boolean(headerRect && (headerRect.left < -1 || headerRect.right > innerWidth + 1)),
        hasCandidateLabel: text.includes('réglette à vérifier'),
        hasAutoAction: text.includes('vérifier automatiquement'),
        hasManualFallback: text.includes('calibrer manuellement'),
        hasWorkspaceHeading: text.includes('studio céphalométrique'),
      };
    });

    const valid = response?.status() === 200 && pageErrors.length === 0 && consoleErrors.length === 0 && !isInvalidMetrics(metrics);
    if (valid) {
      await page.screenshot({ path: path.join(OUTPUT_DIR, `after-cephalo-r1-${viewport.name}.png`), fullPage: false });
    }

    return {
      viewport: viewport.name,
      attempt,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      apiRequests: requests,
      metrics,
      valid,
    };
  } catch (error) {
    return {
      viewport: viewport.name,
      attempt,
      httpStatus: null,
      pageErrors: [...pageErrors, error instanceof Error ? error.message : String(error)],
      consoleErrors,
      apiRequests: requests,
      metrics: {
        innerWidth: viewport.width,
        scrollWidth: null,
        horizontalDocumentOverflow: true,
        assistantRect: null,
        assistantClipped: true,
        headerRect: null,
        headerClipped: true,
        hasCandidateLabel: false,
        hasAutoAction: false,
        hasManualFallback: false,
        hasWorkspaceHeading: false,
      },
      valid: false,
    };
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

try {
  await waitForServer(`${BASE_URL}/cephalo-r1-after.html`);

  for (const viewport of viewports) {
    const attempts = [];
    attempts.push(await captureViewport(viewport, 1));
    if (!attempts[0].valid) attempts.push(await captureViewport(viewport, 2));

    const finalAttempt = attempts.at(-1);
    captures.push({
      ...finalAttempt,
      attempts: attempts.map(item => ({
        attempt: item.attempt,
        valid: item.valid,
        httpStatus: item.httpStatus,
        pageErrors: item.pageErrors,
        consoleErrors: item.consoleErrors,
        metrics: item.metrics,
      })),
      recoveredTransientRender: attempts.length === 2 && !attempts[0].valid && attempts[1].valid,
    });
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  if (server.exitCode === null && !server.killed) server.kill('SIGKILL');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const invalid = captures.filter(item => !item.valid);

const report = {
  lot: 'CEPHALO-R1',
  phase: 'AFTER',
  productHead: PRODUCT_HEAD,
  viewports: viewports.map(item => item.name),
  fixturePolicy: 'Real production CephaloWorkspace/Step1Cephalo with deterministic non-clinical image, isolated patient metadata, and persisted candidate-unverified server state.',
  capturePolicy: 'Fresh Chromium process per viewport. One fresh-process retry is allowed only after a failed first render; the final attempt must independently satisfy every evidence gate.',
  captures,
  blockedExternalRequests,
  invalidCount: invalid.length,
};

await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (invalid.length > 0 || blockedExternalRequests.length > 0) process.exitCode = 1;
