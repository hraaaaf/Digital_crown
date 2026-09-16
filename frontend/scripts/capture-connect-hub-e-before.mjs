import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'connect-hub-e-before-artifacts');
const PORT = 5197;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844, expectBell: true },
  { name: '768x1024', width: 768, height: 1024, expectBell: true },
  { name: '1280x900', width: 1280, height: 900, expectBell: true },
];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { useAuthStore } from './stores/useAuthStore';
import { useSettingsStore } from './features/admin/Settings/hooks/useSettingsStore';
import './index.css';

useAuthStore.setState({
  user: { id: '101', email: 'demo@digitalcrown.local', role: 'ADMIN', nom_complet: 'Dr. Démo', employer_id: null, is_licensed: true },
  isAuthenticated: true,
  isLoading: false,
});
useSettingsStore.setState({
  activeCabinetId: 'demo',
  cabinets: [{ id: 'demo', nom: 'Cabinet Démo', specialty: 'Chirurgien Dentiste', primary_color: '#003380', accent_color: '#60a5fa', theme: 'elite', caisse: 0 }],
  profile: { ...useSettingsStore.getState().profile, nom: 'Dr. Démo', font_fr: 'inter' },
});
localStorage.setItem('active_cabinet_id', 'demo');

document.body.dataset.theme = '';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <MemoryRouter initialEntries={['/dashboard']}>
    <div className="flex h-screen overflow-hidden bg-medical-pearl text-text-main">
      <Sidebar />
      <div className="relative min-w-0 flex-1 overflow-hidden">
        <Header />
        <main className="h-[calc(100vh-5rem)] p-3 sm:p-4 lg:p-8">
          <section className="h-full rounded-elite border border-border-main bg-card-bg/80 p-5 shadow-elite">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary">Tableau de bord</p>
            <h1 className="mt-2 text-2xl font-black">Cabinet Démo</h1>
            <p className="mt-2 text-sm font-semibold text-text-muted">Baseline shell — LOT E</p>
          </section>
        </main>
      </div>
    </div>
  </MemoryRouter>,
);
`;
const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Connect Hub E BEFORE</title><style>html,body,#root{width:100%;height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/connect-hub-e-before-entry.tsx"></script></body></html>`;
const json = (body, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) });

async function waitForServer(url, timeoutMs = 30000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    try { const response = await fetch(url); if (response.ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw new Error(`Vite server unavailable at ${url}`);
}

await rm(OUTPUT_DIR, { recursive: true, force: true });
await rm(path.join(FRONTEND_DIR, 'node_modules', '.vite'), { recursive: true, force: true });
await rm(path.join(FRONTEND_DIR, '.vite'), { recursive: true, force: true });
await mkdir(OUTPUT_DIR, { recursive: true });
await writeFile(path.join(FRONTEND_DIR, 'src', 'connect-hub-e-before-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'connect-hub-e-before.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(PORT), '--force'], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER: 'none', VITE_API_URL: 'http://127.0.0.1:8005' },
  stdio: ['ignore', 'pipe', 'pipe'],
});
let serverLog = '';
server.stdout.on('data', chunk => { serverLog += chunk.toString(); });
server.stderr.on('data', chunk => { serverLog += chunk.toString(); });
const captures = [];
const blockedExternalRequests = [];

async function capture(viewport) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, reducedMotion: 'reduce', locale: 'fr-FR' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
    if (url.hostname === '127.0.0.1' && url.port === '8005') {
      if (url.pathname === '/api/clinics/me') return route.fulfill(json({ nom_cabinet: 'Cabinet Démo', nom_praticien: 'Dr. Démo', header_lines_fr: ['Dr. Démo', 'Chirurgien Dentiste'] }));
      if (url.pathname === '/api/accounting/treasury-hub') return route.fulfill(json({ pending_count: 3 }));
      if (url.pathname === '/api/intelligence/alerts/today') return route.fulfill(json({ total: 5 }));
      return route.fulfill(json({ detail: 'Neutralisé dans le BEFORE visuel' }, 418));
    }
    if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') return route.fulfill({ status: 200, contentType: 'text/css', body: '/* offline */' });
    blockedExternalRequests.push({ viewport: viewport.name, url: request.url(), method: request.method() });
    return route.abort('blockedbyclient');
  });
  try {
    const response = await page.goto(`${BASE_URL}/connect-hub-e-before.html`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.locator('header').waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForTimeout(300);
    const closed = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      hasTreasuryPopover: (document.body.textContent || '').includes('Alertes de trésorerie'),
      hasConnectHub: (document.body.textContent || '').includes('Connect Hub'),
      bellCount: document.querySelectorAll('header button svg.lucide-bell').length,
    }));
    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-shell-${viewport.name}.png`), fullPage: false });

    const bell = page.locator('header button').filter({ has: page.locator('svg.lucide-bell') }).first();
    await bell.click();
    await page.getByText('Alertes de trésorerie', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
    const open = await page.evaluate(() => ({
      innerWidth,
      scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
      hasTreasuryPopover: (document.body.textContent || '').includes('Alertes de trésorerie'),
      hasConnectHub: (document.body.textContent || '').includes('Connect Hub'),
      hasTreasuryAction: (document.body.textContent || '').includes('Relances en attente'),
    }));
    await page.screenshot({ path: path.join(OUTPUT_DIR, `before-bell-open-${viewport.name}.png`), fullPage: false });

    const closedValid = response?.status() === 200 && pageErrors.length === 0 && consoleErrors.length === 0 && closed.bellCount === 1 && !closed.hasTreasuryPopover && !closed.hasConnectHub && closed.scrollWidth <= closed.innerWidth + 1;
    const openValid = open.hasTreasuryPopover && open.hasTreasuryAction && !open.hasConnectHub && open.scrollWidth <= open.innerWidth + 1;
    return { viewport: viewport.name, expectBell: true, httpStatus: response?.status() ?? null, pageErrors, consoleErrors, closed, open, valid: Boolean(closedValid && openValid) };
  } catch (error) {
    return { viewport: viewport.name, expectBell: true, pageErrors: [...pageErrors, error instanceof Error ? error.message : String(error)], consoleErrors, valid: false };
  } finally {
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

try {
  await waitForServer(`${BASE_URL}/connect-hub-e-before.html`);
  for (const viewport of viewports) captures.push(await capture(viewport));
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
}
const invalid = captures.filter(item => !item.valid);
const report = { lot: 'LOT-E-CONNECT-HUB', phase: 'BEFORE', productHead: PRODUCT_HEAD, viewports: viewports.map(v => ({ name: v.name, expectBell: v.expectBell })), fixturePolicy: 'Exact baseline Header + Sidebar production components with deterministic cabinet/treasury/intelligence API fixtures; no target UI injected. All three canonical viewports assert the observed production bell and treasury-only popover.', captures, blockedExternalRequests, invalidCount: invalid.length };
await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (invalid.length || blockedExternalRequests.length) process.exitCode = 1;
