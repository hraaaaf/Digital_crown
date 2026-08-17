import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-installment-baseline');
fs.mkdirSync(outDir, { recursive: true });

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
if (!patient) throw new Error('Patient T2-0001 not found');

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
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  const requestedUrl = `http://127.0.0.1:5173/patients/${patient.id}?tab=finances`;
  await page.goto(requestedUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: /Plan/i }).first().click();
  await page.getByText("Plan d'échéances", { exact: true }).waitFor({ state: 'visible', timeout: 10000 });
  await page.waitForTimeout(250);

  const metrics = await page.evaluate(() => {
    const doc = document.documentElement;
    const modal = [...document.querySelectorAll('div')].find((el) =>
      el.classList.contains('bg-white') &&
      el.classList.contains('max-w-lg') &&
      (el.textContent || '').includes("Plan d'échéances")
    );
    const rect = modal?.getBoundingClientRect();
    return {
      pathname: location.pathname,
      search: location.search,
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
      noPageHorizontalOverflow: doc.scrollWidth <= doc.clientWidth + 2,
      modalFound: Boolean(modal),
      modalRect: rect ? { x: rect.x, y: rect.y, width: rect.width, height: rect.height } : null,
      modalFitsViewport: rect ? rect.x >= -1 && rect.right <= innerWidth + 1 && rect.y >= -1 && rect.bottom <= innerHeight + 1 : false,
      viewport: { width: innerWidth, height: innerHeight },
      bodyTextLength: (document.body.innerText || '').trim().length,
    };
  });

  if (!metrics.modalFound) throw new Error(`Installment modal not found at ${viewport.width}x${viewport.height}`);

  const screenshot = `patient-installment-baseline-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: true });
  evidence.push({ viewport, requestedUrl, metrics, pageErrors, consoleErrors, screenshot });
  await context.close();
}

const summary = {
  patientId: patient.id,
  capturedAt: new Date().toISOString(),
  totalCaptures: evidence.length,
  modalCaptures: evidence.filter((e) => e.metrics.modalFound).length,
  overflowFindings: evidence.filter((e) => !e.metrics.noPageHorizontalOverflow).map((e) => e.viewport),
  modalViewportFitFindings: evidence.filter((e) => !e.metrics.modalFitsViewport).map((e) => e.viewport),
  runtimeErrorFindings: evidence.filter((e) => e.pageErrors.length > 0).map((e) => ({ viewport: e.viewport, errors: e.pageErrors })),
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));

await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
