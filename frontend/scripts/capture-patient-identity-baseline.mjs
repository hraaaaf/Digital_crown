import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-identity-baseline');
fs.mkdirSync(outDir, { recursive: true });
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password: 'T2BrowserPass123!' } });
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const patients = await api.get('/api/patients', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((p) => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2-0001 patient not found');

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
  for (const surface of ['add', 'edit']) {
    const context = await browser.newContext({ viewport, colorScheme: 'light' });
    const page = await context.newPage();
    await seedAuth(page);
    const pageErrors = [];
    const consoleErrors = [];
    page.on('pageerror', (e) => pageErrors.push(String(e)));
    page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });

    const url = surface === 'add'
      ? 'http://127.0.0.1:5173/patients/new'
      : `http://127.0.0.1:5173/patients/${patient.id}/edit`;
    await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
    await page.waitForTimeout(500);
    const expected = surface === 'add' ? 'Nouveau Patient' : 'Mise à jour';
    await page.getByText(expected, { exact: true }).waitFor({ state: 'visible', timeout: 30000 });

    const metrics = await page.evaluate(() => {
      const doc = document.documentElement;
      const select = document.querySelector('select[name="sexe"]');
      return {
        pathname: location.pathname,
        noHorizontalOverflow: doc.scrollWidth <= doc.clientWidth + 2,
        sexValue: select instanceof HTMLSelectElement ? select.value : null,
      };
    });
    const screenshot = `patient-identity-${surface}-baseline-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outDir, screenshot), fullPage: true });
    evidence.push({ surface, viewport, metrics, pageErrors, consoleErrors, screenshot });
    await context.close();
  }
}

const summary = {
  totalCaptures: evidence.length,
  overflowFindings: evidence.filter((e) => !e.metrics.noHorizontalOverflow),
  runtimeErrorFindings: evidence.filter((e) => e.pageErrors.length || e.consoleErrors.length),
  addDefaultSexValues: evidence.filter((e) => e.surface === 'add').map((e) => ({ viewport: e.viewport, value: e.metrics.sexValue })),
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));

if (summary.totalCaptures !== 8 || summary.overflowFindings.length || summary.runtimeErrorFindings.length) {
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
}
await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
