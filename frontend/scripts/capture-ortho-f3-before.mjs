import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';

const PRODUCT_HEAD = process.env.PRODUCT_HEAD || 'unknown';
const FRONTEND_DIR = process.cwd();
const OUTPUT_DIR = path.join(FRONTEND_DIR, 'ortho-f3-before-artifacts');
const PORT = 5196;
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
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PatientJourney } from './features/patients/components/PatientJourney';
import './index.css';

const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={client}>
    <MemoryRouter initialEntries={['/patients/915?tab=tracking']}>
      <main style={{maxWidth: '1200px', margin: '0 auto', padding: '24px 16px'}}>
        <PatientJourney patientId={915} />
      </main>
    </MemoryRouter>
  </QueryClientProvider>
);
`;

const htmlSource = `<!doctype html><html lang="fr"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>Ortho F3 BEFORE</title><style>html,body,#root{width:100%;min-height:100%;margin:0}</style></head><body><div id="root"></div><script type="module" src="/src/ortho-f3-before-entry.tsx"></script></body></html>`;

const journey = {
  patient_id: 915,
  window_months: 12,
  truncated: false,
  total_events_available: 5,
  summary: {
    active_plan_steps: 1,
    total_plan_steps: 4,
    remaining_due: 0,
    has_billing_data: false,
    next_appointment: '2026-10-12T10:00:00',
    last_document_date: '2026-09-18T11:00:00',
  },
  events: [
    { event_key:'ortho_timepoint:11', source:'ortho_timepoint', type:'T1', ref_id:11, date:'2026-09-18T10:00:00', title:'Timepoint orthodontique T1', status:'ENREGISTRE', phase_hint:'ortho', navigation_target:'INLINE', related_event_key:null },
    { event_key:'ortho_control:21', source:'ortho_control', type:'CONTROLE', ref_id:21, date:'2026-09-18T09:00:00', title:'Contrôle orthodontique — Alignement', status:'ENREGISTRE', phase_hint:'alignement', navigation_target:'INLINE', related_event_key:null },
    { event_key:'ortho_timepoint:10', source:'ortho_timepoint', type:'T0', ref_id:10, date:'2026-03-18T10:00:00', title:'Timepoint orthodontique T0', status:'ENREGISTRE', phase_hint:'ortho', navigation_target:'INLINE', related_event_key:null },
    { event_key:'cephalo_analysis:31', source:'cephalo_analysis', type:'cephalometrie', ref_id:31, date:'2026-03-18T10:00:00', title:'Analyse céphalométrique', status:'CALIBRE', phase_hint:'radio', navigation_target:'RADIOLOGY_TAB', related_event_key:null },
    { event_key:'appointment:40', source:'appointment', type:'consultation', ref_id:40, date:'2026-02-12T10:00:00', title:'Consultation orthodontique', status:'TERMINE', phase_hint:'consultation', navigation_target:'INLINE', related_event_key:null },
  ],
};

function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}
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
await writeFile(path.join(FRONTEND_DIR, 'src', 'ortho-f3-before-entry.tsx'), entrySource, 'utf8');
await writeFile(path.join(FRONTEND_DIR, 'ortho-f3-before.html'), htmlSource, 'utf8');

const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', process.platform === 'win32' ? 'vite.cmd' : 'vite');
const server = spawn(viteBin, ['--host','127.0.0.1','--port',String(PORT)], {
  cwd: FRONTEND_DIR,
  env: { ...process.env, BROWSER:'none', VITE_API_URL:'http://127.0.0.1:8005' },
  stdio:['ignore','pipe','pipe'],
});
let serverLog = '';
server.stdout.on('data', c => { serverLog += c.toString(); });
server.stderr.on('data', c => { serverLog += c.toString(); });

const captures = [];
const blockedExternalRequests = [];

for (const viewport of viewports) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport:{width:viewport.width,height:viewport.height}, reducedMotion:'reduce', locale:'fr-FR' });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => pageErrors.push(e.message));

  await page.route('**/*', async route => {
    const req = route.request();
    const url = new URL(req.url());
    if (url.hostname === '127.0.0.1' && url.port === String(PORT)) return route.continue();
    if (url.hostname === '127.0.0.1' && url.port === '8005') {
      if (req.method() === 'GET' && url.pathname === '/api/patients/915/journey') return route.fulfill(json(journey));
      if (req.method() === 'GET' && url.pathname === '/api/actes/patient/915') return route.fulfill(json([]));
      if (req.method() === 'GET' && url.pathname === '/api/patients/915/documents') return route.fulfill(json([]));
      return route.fulfill(json({ detail:'Endpoint neutralisé dans le BEFORE F3' },418));
    }
    if (url.hostname === 'fonts.googleapis.com') return route.fulfill({status:200,contentType:'text/css',body:'/* offline */'});
    blockedExternalRequests.push({viewport:viewport.name,url:req.url(),method:req.method()});
    return route.abort('blockedbyclient');
  });

  try {
    await waitForServer(`${BASE_URL}/ortho-f3-before.html`);
    const response = await page.goto(`${BASE_URL}/ortho-f3-before.html`, { waitUntil:'domcontentloaded', timeout:30000 });
    await page.getByText('Prochaine action').waitFor({state:'visible',timeout:30000});
    await page.waitForTimeout(350);
    const metrics = await page.evaluate(() => {
      const bodyText = (document.body.textContent || '').toLowerCase();
      const doc = document.documentElement;
      return {
        innerWidth,
        scrollWidth: Math.max(doc.scrollWidth, document.body.scrollWidth),
        horizontalOverflow: Math.max(doc.scrollWidth, document.body.scrollWidth) > innerWidth + 1,
        hasCompareSurface: bodyText.includes('comparaison orthodontique'),
        hasT0Visible: bodyText.includes('timepoint orthodontique t0'),
        hasT1Visible: bodyText.includes('timepoint orthodontique t1'),
        hasJourney: bodyText.includes('prochaine action'),
        hasRadioGroup: bodyText.includes('radios & analyses'),
      };
    });
    const valid = response?.status() === 200 && !metrics.horizontalOverflow && metrics.hasJourney && !metrics.hasCompareSurface && !metrics.hasT0Visible && !metrics.hasT1Visible && consoleErrors.length === 0 && pageErrors.length === 0;
    await page.screenshot({ path:path.join(OUTPUT_DIR,`before-overview-${viewport.name}.png`), fullPage:true });
    captures.push({viewport:viewport.name,httpStatus:response?.status()??null,metrics,consoleErrors,pageErrors,valid});
  } catch (error) {
    captures.push({viewport:viewport.name,httpStatus:null,metrics:null,consoleErrors,pageErrors:[...pageErrors,error instanceof Error?error.message:String(error)],valid:false});
  } finally {
    await context.close().catch(()=>{});
    await browser.close().catch(()=>{});
  }
}

if (!server.killed) server.kill('SIGTERM');
await Promise.race([once(server,'exit'),new Promise(resolve=>setTimeout(resolve,3000))]).catch(()=>{});
await writeFile(path.join(OUTPUT_DIR,'vite.log'),serverLog,'utf8');
const invalid = captures.filter(c => !c.valid);
const report = {
  lot:'V1-05-F3',
  phase:'BEFORE',
  productHead:PRODUCT_HEAD,
  viewports:viewports.map(v=>v.name),
  fixturePolicy:'Exact merged F2 PatientJourney with deterministic API fixture containing T0/T1 events. No F3 UI injected.',
  captures,
  blockedExternalRequests,
  invalidCount:invalid.length,
};
await writeFile(path.join(OUTPUT_DIR,'report.json'),JSON.stringify(report,null,2),'utf8');
console.log(JSON.stringify(report,null,2));
if (invalid.length || blockedExternalRequests.length) process.exitCode = 1;
