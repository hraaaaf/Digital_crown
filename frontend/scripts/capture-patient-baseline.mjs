import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-baseline');
fs.mkdirSync(outDir, { recursive: true });

const tabs = [
  { slug: 'tracking', label: 'Séances & Suivi' },
  { slug: 'clinical', label: 'Examen Clinique' },
  { slug: 'radiology', label: 'Radiologie (IA)' },
  { slug: 'admin', label: 'Documents A5' },
  { slug: 'archives', label: 'Archives & Historique' },
  { slug: 'finances', label: 'Finances' },
];

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password: 'T2BrowserPass123!' },
});
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const patients = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patientList = await patients.json();
const patient = patientList.find((p) => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('Patient baseline certification patient not found');

const browser = await chromium.launch({ headless: true });
const evidence = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);

  for (const tab of tabs) {
    const pageErrors = [];
    const consoleErrors = [];
    const onPageError = (error) => pageErrors.push(String(error));
    const onConsole = (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    };
    page.on('pageerror', onPageError);
    page.on('console', onConsole);

    const requestedUrl = `http://127.0.0.1:5173/patients/${patient.id}?tab=${tab.slug}`;
    await page.goto(requestedUrl, { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForTimeout(500);

    const metrics = await page.evaluate(({ expectedTab }) => {
      const doc = document.documentElement;
      const params = new URLSearchParams(location.search);
      return {
        pathname: location.pathname,
        search: location.search,
        requestedTabPreserved: params.get('tab') === expectedTab,
        patientRouteVisible: location.pathname.startsWith('/patients/'),
        scrollWidth: doc.scrollWidth,
        clientWidth: doc.clientWidth,
        noHorizontalOverflow: doc.scrollWidth <= doc.clientWidth + 2,
        bodyTextLength: (document.body.innerText || '').trim().length,
      };
    }, { expectedTab: tab.slug });

    const screenshot = `patient-baseline-${viewport.width}x${viewport.height}-${tab.slug}.png`;
    await page.screenshot({ path: path.join(outDir, screenshot), fullPage: true });

    evidence.push({
      tab,
      viewport,
      requestedUrl,
      metrics,
      pageErrors,
      consoleErrors,
      screenshot,
    });

    page.off('pageerror', onPageError);
    page.off('console', onConsole);
  }

  await context.close();
}

const summary = {
  patientId: patient.id,
  capturedAt: new Date().toISOString(),
  viewports: viewports.map((v) => `${v.width}x${v.height}`),
  tabs: tabs.map((t) => t.slug),
  totalCaptures: evidence.length,
  patientRouteCaptures: evidence.filter((e) => e.metrics.patientRouteVisible).length,
  redirectedCaptures: evidence.filter((e) => !e.metrics.patientRouteVisible).length,
  overflowFindings: evidence.filter((e) => !e.metrics.noHorizontalOverflow).map((e) => ({ tab: e.tab.slug, viewport: e.viewport })),
  runtimeErrorFindings: evidence.filter((e) => e.pageErrors.length > 0).map((e) => ({ tab: e.tab.slug, viewport: e.viewport, errors: e.pageErrors })),
};

fs.writeFileSync(path.join(outDir, 'baseline-evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'baseline-summary.json'), JSON.stringify(summary, null, 2));

await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
