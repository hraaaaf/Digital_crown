import { chromium } from 'playwright';
import { createServer } from 'vite';
import fs from 'node:fs/promises';

const output = 'mobile-m4a-before-artifacts';
await fs.mkdir(output, { recursive: true });
const server = await createServer({ server: { host: '127.0.0.1', port: 4179, strictPort: true }, clearScreen: false });
await server.listen();
const browser = await chromium.launch();
const results = [];
const json = body => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const patient = {
  id: 42,
  numero_dossier: 'DC-0042',
  nom: 'BENNANI',
  prenom: 'Sara',
  date_naissance: '1992-05-18',
  telephone: '0612345678',
  email: 'sara.bennani@example.test',
  adresse: 'Rabat',
  assurance: 'MUTUELLE',
  antecedents_medicaux: 'Allergie pénicilline',
  motif_consultation: 'Contrôle',
  dossier: { is_ortho_active: false },
};
const journey = {
  patient_id: 42,
  window_months: 12,
  truncated: false,
  total_events_available: 0,
  summary: {
    active_plan_steps: 0,
    total_plan_steps: 0,
    remaining_due: 0,
    has_billing_data: false,
    next_appointment: null,
    last_document_date: null,
  },
  events: [],
};
const snapshot = {
  generated_at: '2026-08-24T19:30:00Z',
  role: 'ADMIN',
  is_superadmin: false,
  appointments: [],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: 0,
    appointments_count: 0,
    weekly_revenue: [],
    total_patients: 1,
    total_debt: 0,
  },
  debtors: [],
};

async function contextFor(viewport) {
  const context = await browser.newContext({
    viewport,
    screen: viewport,
    deviceScaleFactor: 1,
    hasTouch: viewport.width <= 768,
    isMobile: viewport.width <= 768,
    serviceWorkers: 'block',
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(`pageerror: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') errors.push(`console: ${m.text()}`); });
  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    if (!url.pathname.startsWith('/api/')) return route.continue();
    const path = url.pathname;
    if (path === '/api/patients/42') return route.fulfill(json(patient));
    if (path === '/api/patients/42/journey') return route.fulfill(json(journey));
    if (path === '/api/actes/patient/42') return route.fulfill(json([]));
    if (path === '/api/patients/42/documents') return route.fulfill(json([]));
    if (path === '/api/intelligence/patient/42/nba') return route.fulfill(json({ nba: null }));
    if (path === '/api/mobile/snapshot') return route.fulfill(json(snapshot));
    if (path === '/api/mobile/patients') return route.fulfill(json({ data: [] }));
    if (path === '/api/lab-jobs/') return route.fulfill(json([]));
    if (path === '/api/mobile/refresh-token') return route.fulfill({ status: 401, contentType: 'application/json', body: '{}' });
    return route.fulfill(json(request.method() === 'GET' ? [] : {}));
  });
  return { context, page, errors };
}

async function metrics(page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    const controls = [...document.querySelectorAll('button, input, select, a')]
      .filter(el => {
        const style = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return style.visibility !== 'hidden' && style.display !== 'none' && r.width > 0 && r.height > 0;
      })
      .map(el => {
        const r = el.getBoundingClientRect();
        return {
          tag: el.tagName,
          text: (el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 120),
          width: Math.round(r.width),
          height: Math.round(r.height),
        };
      });
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
      hasHorizontalOverflow: root.scrollWidth > root.clientWidth + 1,
      controlsBelow44: controls.filter(c => c.height < 44),
      bridgeButtonPresent: [...document.querySelectorAll('button,a')].some(el => /ouvrir sur mobile/i.test(el.textContent || el.getAttribute('aria-label') || '')),
      patientContextRoutePresent: location.pathname === '/mobile/context',
    };
  });
}

async function capture(page, errors, name, state, viewport) {
  const measured = await metrics(page);
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: false, animations: 'disabled' });
  const record = { name, state, ...viewport, metrics: measured, errors: [...errors] };
  results.push(record);
  await fs.writeFile(`${output}/${name}.json`, JSON.stringify(record, null, 2));
}

try {
  for (const viewport of [{ width: 1280, height: 900 }, { width: 768, height: 1024 }]) {
    const { context, page, errors } = await contextFor(viewport);
    await page.goto('http://127.0.0.1:4179/mobile-m4a-before.html?view=patient', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'BENNANI Sara', exact: true }).waitFor({ state: 'visible', timeout: 15000 });
    await capture(page, errors, `patient-desktop-${viewport.width}x${viewport.height}`, 'patient-desktop-before', viewport);
    await context.close();
  }

  for (const viewport of [{ width: 390, height: 844 }, { width: 430, height: 932 }, { width: 768, height: 1024 }]) {
    const { context, page, errors } = await contextFor(viewport);
    await page.goto('http://127.0.0.1:4179/mobile-m4a-before.html?view=mobile', { waitUntil: 'networkidle' });
    await page.getByText('Agenda', { exact: true }).first().waitFor({ state: 'visible', timeout: 15000 });
    await capture(page, errors, `mobile-generic-${viewport.width}x${viewport.height}`, 'mobile-generic-before', viewport);
    await context.close();
  }
} finally {
  await browser.close();
  await server.close();
}

const report = {
  baselineHead: process.env.BASELINE_HEAD,
  captures: results,
  bridgeAbsent: results.filter(r => r.state === 'patient-desktop-before').every(r => r.metrics.bridgeButtonPresent === false),
  exactPatientMobileAbsent: results.filter(r => r.state === 'mobile-generic-before').every(r => r.metrics.patientContextRoutePresent === false),
};
await fs.writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));

const failures = results.filter(r => r.errors.length || r.metrics.hasHorizontalOverflow);
if (results.length !== 5 || failures.length || !report.bridgeAbsent || !report.exactPatientMobileAbsent) {
  console.error(JSON.stringify({ results: results.length, failures, bridgeAbsent: report.bridgeAbsent, exactPatientMobileAbsent: report.exactPatientMobileAbsent }, null, 2));
  process.exitCode = 1;
}
console.log(JSON.stringify({ captures: results.length, failures: failures.length, bridgeAbsent: report.bridgeAbsent, exactPatientMobileAbsent: report.exactPatientMobileAbsent }, null, 2));
