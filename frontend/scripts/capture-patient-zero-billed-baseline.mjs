import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-zero-billed-baseline');
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
const patients = await api.get('/api/patients', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((p) => p.numero_dossier === 'T2-ZERO-BILL');
if (!patient) throw new Error('T2-ZERO-BILL patient not found');

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
  page.on('pageerror', (error) => pageErrors.push(String(error)));

  const url = `http://127.0.0.1:5173/patients/${patient.id}?tab=finances`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Taux Recouvrement', { exact: true }).waitFor({ state: 'visible' });

  const metrics = await page.evaluate(() => {
    const body = document.body.innerText || '';
    const doc = document.documentElement;
    return {
      hasZeroBilled: body.includes('Total Facturé') && body.includes('0'),
      hasCollected800: body.includes('800'),
      showsRecovery100: body.includes('100%'),
      noHorizontalOverflow: doc.scrollWidth <= doc.clientWidth + 2,
    };
  });

  const screenshot = `patient-zero-billed-baseline-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: true });
  evidence.push({ viewport, metrics, pageErrors, screenshot });
  await context.close();
}

const summary = {
  patientId: patient.id,
  totalCaptures: evidence.length,
  recovery100Findings: evidence.filter((e) => e.metrics.showsRecovery100).map((e) => e.viewport),
  overflowFindings: evidence.filter((e) => !e.metrics.noHorizontalOverflow).map((e) => e.viewport),
  runtimeErrorFindings: evidence.filter((e) => e.pageErrors.length).map((e) => ({ viewport: e.viewport, errors: e.pageErrors })),
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));

if (summary.recovery100Findings.length !== viewports.length) {
  console.error('Baseline no longer demonstrates the 100% zero-billed defect');
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
}

await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
