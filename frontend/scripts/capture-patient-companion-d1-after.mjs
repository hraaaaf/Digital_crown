import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'patient-companion-d1-after-artifacts');
const ENTRY_PATH = path.join(FRONTEND_DIR, 'src', 'patient-companion-d1-after-entry.tsx');
const HTML_PATH = path.join(FRONTEND_DIR, 'patient-companion-d1-after.html');
const PORT = 5198;
const BASE_URL = `http://127.0.0.1:${PORT}`;
const viewports = [
  { name: '390x844', width: 390, height: 844 },
  { name: '768x1024', width: 768, height: 1024 },
  { name: '1280x900', width: 1280, height: 900 },
];
const states = ['public-entry', 'home', 'activation'];

const entrySource = `
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { PatientCompanionPage } from './pages/PatientCompanionPage';
import { PatientCompanionApiError } from './patient-companion/patientCompanionApi';
import './index.css';

document.body.dataset.theme = 'light';
const state = new URLSearchParams(window.location.search).get('state') || 'home';
const verifiedUser = { uid: 'visual-patient', email: 'nadia@example.test', emailVerified: true };
const context = {
  access_id: 'visual-access',
  relationship_type: 'SELF',
  patient: { display_name: 'Nadia El Amrani', prenom: 'Nadia', nom: 'El Amrani' },
};
const services = {
  auth: {
    configured: () => true,
    observe: async (listener) => { listener(verifiedUser); return () => {}; },
    signIn: async () => verifiedUser,
    create: async () => verifiedUser,
    resendVerification: async () => {},
    refresh: async () => verifiedUser,
    signOut: async () => {},
  },
  api: {
    getContexts: async () => {
      if (state === 'activation') throw new PatientCompanionApiError(403, 'Aucun accès patient actif.');
      return [context];
    },
    activate: async () => context,
    getAppointments: async () => [
      { id: 1, datetime_start: '2026-09-21T10:30:00', duration_minutes: 30, motif: 'Contrôle', status: 'PLANIFIE', scheduling_type: 'CONSULTATION' },
      { id: 2, datetime_start: '2026-10-08T15:00:00', duration_minutes: 45, motif: 'Suivi', status: 'PLANIFIE', scheduling_type: 'CONTROLE' },
    ],
    getShares: async () => [
      { share_id: 'doc-1', resource_type: 'document', resource_id: 11, title: 'Compte rendu de consultation', document_type: 'COURRIER' },
      { share_id: 'media-1', resource_type: 'media', resource_id: 12, asset_type: 'PHOTO', mime_type: 'image/jpeg' },
    ],
  },
  initialToken: state === 'activation' ? 'visual-opaque-token' : '',
};
const node = state === 'public-entry'
  ? <MemoryRouter initialEntries={['/landing']}><LandingPage /></MemoryRouter>
  : <PatientCompanionPage services={services} />;
ReactDOM.createRoot(document.getElementById('root')).render(node);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Patient Companion D1 AFTER</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/patient-companion-d1-after-entry.tsx"></script></body></html>`;

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
await writeFile(ENTRY_PATH, entrySource, 'utf8');
await writeFile(HTML_PATH, htmlSource, 'utf8');

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
  await waitForServer(`${BASE_URL}/patient-companion-d1-after.html`);
  for (const state of states) {
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
        blockedExternalRequests.push({ state, viewport: viewport.name, url: route.request().url(), method: route.request().method() });
        return route.abort('blockedbyclient');
      });

      const response = await page.goto(`${BASE_URL}/patient-companion-d1-after.html?state=${state}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      if (state === 'public-entry') {
        await page.getByText('DigitalCrown').first().waitFor({ state: 'visible', timeout: 30000 });
        await page.getByText(/Logiciel dentaire nouvelle génération/i).waitFor({ state: 'visible', timeout: 30000 });
      } else {
        await page.getByText('Patient Companion').first().waitFor({ state: 'visible', timeout: 30000 });
        if (state === 'home') {
          await page.getByText('Prochains rendez-vous').waitFor({ state: 'visible', timeout: 30000 });
          await page.getByText('Éléments partagés').waitFor({ state: 'visible', timeout: 30000 });
        } else {
          await page.getByText('Activer mon espace patient').waitFor({ state: 'visible', timeout: 30000 });
        }
      }
      await page.evaluate(async () => { if (document.fonts?.ready) await document.fonts.ready; });
      await page.waitForTimeout(150);

      const metrics = await page.evaluate(({ viewportName, visualState }) => {
        const body = document.body;
        const doc = document.documentElement;
        const text = (body.textContent || '').toLowerCase();
        const scrollWidth = Math.max(doc.scrollWidth, body.scrollWidth);
        return {
          state: visualState,
          viewport: viewportName,
          innerWidth,
          scrollWidth,
          horizontalDocumentOverflow: scrollWidth > innerWidth + 1,
          hasBrand: text.includes('digitalcrown'),
          hasLandingHero: text.includes('logiciel dentaire nouvelle génération'),
          hasPatientCompanion: text.includes('patient companion'),
          hasActivation: text.includes('activer mon espace patient'),
          hasAppointments: text.includes('prochains rendez-vous'),
          hasShares: text.includes('éléments partagés'),
          hasStaffNavigation: text.includes('approvisionnement') || text.includes('science hub') || text.includes('super-admin'),
        };
      }, { viewportName: viewport.name, visualState: state });

      let stateValid = false;
      if (state === 'public-entry') {
        stateValid = metrics.hasBrand && metrics.hasLandingHero && !metrics.hasPatientCompanion && !metrics.hasActivation;
      } else if (state === 'home') {
        stateValid = metrics.hasPatientCompanion && metrics.hasAppointments && metrics.hasShares && !metrics.hasActivation && !metrics.horizontalDocumentOverflow;
      } else {
        stateValid = metrics.hasPatientCompanion && metrics.hasActivation && !metrics.hasAppointments && !metrics.horizontalDocumentOverflow;
      }
      const valid = response?.status() === 200
        && pageErrors.length === 0
        && consoleErrors.length === 0
        && !metrics.hasStaffNavigation
        && stateValid;

      await page.screenshot({ path: path.join(OUTPUT_DIR, `after-${state}-${viewport.name}.png`), fullPage: false });
      captures.push({ state, viewport: viewport.name, httpStatus: response?.status() ?? null, pageErrors, consoleErrors, metrics, valid });
      await context.close();
      await browser.close();
    }
  }
} finally {
  if (!server.killed) server.kill('SIGTERM');
  await Promise.race([once(server, 'exit'), new Promise(resolve => setTimeout(resolve, 3000))]).catch(() => {});
  await writeFile(path.join(OUTPUT_DIR, 'vite.log'), serverLog, 'utf8');
  await rm(ENTRY_PATH, { force: true });
  await rm(HTML_PATH, { force: true });
}

const invalid = captures.filter(item => !item.valid);
const report = {
  lot: 'PATIENT-COMPANION-D1',
  phase: 'AFTER',
  productHead: PRODUCT_HEAD,
  viewports: viewports.map(item => item.name),
  states,
  baselineComparableState: 'public-entry',
  captures,
  blockedExternalRequests,
  invalidCount: invalid.length,
};
await writeFile(path.join(OUTPUT_DIR, 'report.json'), JSON.stringify(report, null, 2), 'utf8');
console.log(JSON.stringify(report, null, 2));
if (invalid.length > 0 || blockedExternalRequests.length > 0) process.exitCode = 1;
