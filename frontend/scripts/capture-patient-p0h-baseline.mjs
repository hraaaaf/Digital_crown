import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-p0h-baseline');
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
if (!patient) throw new Error('P0-H certification patient not found');

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

  const requestedUrl = `http://127.0.0.1:5173/patients/${patient.id}?tab=tracking`;
  await page.goto(requestedUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(700);

  const metrics = await page.evaluate(() => {
    const header = document.querySelector('header');
    const text = header?.textContent || '';
    const scoreWords = ['Platinum', 'Gold', 'Silver', 'Bronze'];
    return {
      pathname: location.pathname,
      headerVisible: Boolean(header),
      headerText: text.replace(/\s+/g, ' ').trim(),
      scoreWordVisible: scoreWords.some((word) => text.includes(word)),
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      noHorizontalOverflow: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
    };
  });

  const screenshot = `patient-p0h-baseline-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });
  evidence.push({ viewport, requestedUrl, metrics, pageErrors, screenshot });
  await context.close();
}

const summary = {
  patientId: patient.id,
  capturedAt: new Date().toISOString(),
  totalCaptures: evidence.length,
  headerMissing: evidence.filter((e) => !e.metrics.headerVisible),
  overflowFindings: evidence.filter((e) => !e.metrics.noHorizontalOverflow).map((e) => e.viewport),
  runtimeErrorFindings: evidence.filter((e) => e.pageErrors.length).map((e) => ({ viewport: e.viewport, errors: e.pageErrors })),
  scoreWordFindings: evidence.filter((e) => e.metrics.scoreWordVisible).map((e) => e.viewport),
};

fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
