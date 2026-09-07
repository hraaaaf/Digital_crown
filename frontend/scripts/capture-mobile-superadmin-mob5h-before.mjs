import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const BASELINE_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'mobile-superadmin-mob5h-before-artifacts');
const PORT = 5183;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '430x932', width: 430, height: 932 },
  { name: '768x1024', width: 768, height: 1024 },
];

const clients = [
  {
    id: 501,
    nom_complet: 'Dr Démo Atlas',
    email: 'atlas@example.test',
    cabinet_name: 'Cabinet Atlas Démo',
    is_licensed: true,
    license_expires_at: '2030-10-01T00:00:00Z',
    is_archived: false,
    is_suspended: false,
    subscription_plan: 'ELITE',
    stats: { total_patients: 128, total_ia_panoramique: 42, total_ia_cephalo: 17 },
  },
  {
    id: 502,
    nom_complet: 'Dr Démo Rivage',
    email: 'rivage@example.test',
    cabinet_name: 'Cabinet Rivage Démo',
    is_licensed: true,
    license_expires_at: '2026-09-12T00:00:00Z',
    is_archived: false,
    is_suspended: false,
    subscription_plan: 'PREMIUM',
    stats: { total_patients: 81, total_ia_panoramique: 11, total_ia_cephalo: 4 },
  },
  {
    id: 503,
    nom_complet: 'Dr Démo Oasis',
    email: 'oasis@example.test',
    cabinet_name: 'Cabinet Oasis Démo',
    is_licensed: true,
    license_expires_at: '2030-12-31T00:00:00Z',
    is_archived: false,
    is_suspended: true,
    subscription_plan: 'GOLD',
    stats: { total_patients: 54, total_ia_panoramique: 7, total_ia_cephalo: 2 },
  },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { MobileStorage } from './services/zka/MobileStorage';
import { MobileSuperAdminView } from './features/mobile/Dashboard/views/MobileSuperAdminView';
import './index.css';
import './styles/mobileGlassSystem.css';
import './features/mobile/mobileRuntimeTheme.css';

function base64Url(value: string) {
  return btoa(value).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/g, '');
}

async function bootstrap() {
  await MobileStorage.clearAll();
  const token = [
    base64Url(JSON.stringify({ alg: 'none', typ: 'JWT' })),
    base64Url(JSON.stringify({ sub: 'mob5h-before', exp: 1924992000 })),
    'preview',
  ].join('.');
  await MobileStorage.saveCredentials({
    publicId: '0123456789abcdef',
    masterKey: '${'a'.repeat(64)}',
    access_token: token,
    refresh_token: 'preview-refresh-token',
    device_id: 'mob5h-before-device',
    api_base_url: 'http://127.0.0.1:8005',
  });
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <MemoryRouter initialEntries={['/mobile/superadmin']}>
      <MobileSuperAdminView />
    </MemoryRouter>,
  );
}

void bootstrap();
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>MOB-5H BEFORE</title></head><body><div id="root"></div><script type="module" src="/src/mob5h-before-entry.tsx"></script></body></html>`;

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
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'mob5h-before-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'mob5h-before.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', (chunk) => { serverLog += chunk.toString(); });
server.stderr.on('data', (chunk) => { serverLog += chunk.toString(); });

let browser;
const captures = [];
const allApiRequests = [];
const neutralizedExternalRequests = [];
const blockedExternalRequests = [];

try {
  await waitForServer(`${BASE_URL}/mob5h-before.html`);
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
    const apiRequests = [];

    page.on('pageerror', (error) => pageErrors.push(error.message));
    page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });

    await page.route('**/*', async (route) => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
      if (url.hostname === '127.0.0.1' && url.port === '8005') {
        const record = `${request.method()} ${url.pathname}${url.search}`;
        apiRequests.push(record);
        allApiRequests.push({ viewport: viewport.name, request: record });
        if (request.method() === 'GET' && url.pathname === '/api/superadmin/clients') {
          return route.fulfill(json(clients));
        }
        return route.fulfill(json({ detail: 'Endpoint interdit dans le BEFORE' }, 418));
      }
      if (url.hostname === 'fonts.googleapis.com') {
        neutralizedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method(), mode: 'offline-css-shim' });
        return route.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* MOB-5H offline visual harness: external fonts intentionally neutralized. */' });
      }
      blockedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method() });
      return route.abort('blockedbyclient');
    });

    const response = await page.goto(`${BASE_URL}/mob5h-before.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.getByRole('heading', { name: 'SuperAdmin' }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByText('Dr Démo Atlas').waitFor({ state: 'visible', timeout: 30000 });

    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      const body = document.body;
      const heading = Array.from(document.querySelectorAll('h1')).find((node) => node.textContent?.includes('SuperAdmin'));
      const search = document.querySelector('input[placeholder="Rechercher un client..."]');
      const firstCard = Array.from(document.querySelectorAll('p')).find((node) => node.textContent === 'Dr Démo Atlas')?.closest('div.bg-card');
      const buttons = Array.from(document.querySelectorAll('button')).map((node) => (node.textContent || '').trim()).filter(Boolean);
      return {
        innerWidth,
        scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
        horizontalOverflow: Math.max(doc.scrollWidth, body.scrollWidth) > innerWidth + 1,
        headingInFirstViewport: Boolean(heading && heading.getBoundingClientRect().top < innerHeight),
        searchInFirstViewport: Boolean(search && search.getBoundingClientRect().top < innerHeight),
        firstClientInFirstViewport: Boolean(firstCard && firstCard.getBoundingClientRect().top < innerHeight),
        hasPlanControl: Boolean(document.querySelector('select')),
        visibleActionLabels: buttons,
        bodyText: body.innerText,
      };
    });

    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-mobile-${viewport.name}.png`), fullPage: false });
    captures.push({
      viewport: viewport.name,
      httpStatus: response?.status() ?? null,
      pageErrors,
      consoleErrors,
      apiRequests,
      metrics,
    });
    await context.close();
  }
} finally {
  if (browser) await browser.close();
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise((resolve) => setTimeout(resolve, 3000))]).catch(() => {});
  if (server.exitCode === null && !server.killed) server.kill('SIGKILL');
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}

const invalid = captures.filter((item) =>
  item.httpStatus !== 200 ||
  item.pageErrors.length > 0 ||
  item.consoleErrors.length > 0 ||
  item.metrics.horizontalOverflow ||
  !item.metrics.headingInFirstViewport ||
  !item.metrics.searchInFirstViewport ||
  !item.metrics.firstClientInFirstViewport ||
  !item.metrics.hasPlanControl ||
  item.apiRequests.length !== 1 ||
  item.apiRequests[0] !== 'GET /api/superadmin/clients'
);

const report = {
  lot: 'MOB-5H',
  phase: 'BEFORE',
  baselineProductHead: BASELINE_HEAD,
  viewports: viewports.map((item) => item.name),
  captures,
  allApiRequests,
  neutralizedExternalRequests,
  blockedExternalRequests,
  realExternalEgressAllowed: false,
  invalidCount: invalid.length,
  baselineCapabilitiesObserved: {
    clientListSearch: true,
    planChange: true,
    licenseExtension: true,
    suspendReactivate: true,
    dedicatedClientDetail: false,
    trialCodes: false,
    revokeLicense: false,
    archive: false,
    internalNotes: false,
    licenseHistory: false,
    renewalAction: false,
    marketplaceGovernance: false,
    marketplaceOperations: false,
  },
};

await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
if (invalid.length > 0 || blockedExternalRequests.length > 0) {
  console.error(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} else {
  console.log(JSON.stringify(report, null, 2));
}
