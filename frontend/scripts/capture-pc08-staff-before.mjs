import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const apiUrl = process.env.PC08_API_URL || 'http://127.0.0.1:8005';
const appUrl = process.env.PC08_APP_URL || 'http://127.0.0.1:5173';
const outDir = path.resolve(process.env.PC08_STAFF_BEFORE_DIR || '../artifacts/pc08-staff-before');
const user = process.env.T2_USER;
const pass = process.env.T2_PASSWORD;
if (!user || !pass) throw new Error('isolated staff credentials missing');

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const api = await request.newContext({ baseURL: apiUrl });
const login = await api.post('/api/auth/login', { form: { username: user, password: pass } });
if (!login.ok()) throw new Error('staff login failed');
const tokens = await login.json();
const patientsResponse = await api.get('/api/patients', {
  headers: { Authorization: `Bearer ${tokens.access_token}` },
});
if (!patientsResponse.ok()) throw new Error('patient list failed');
const patients = await patientsResponse.json();
const patient = patients.find(item => item.numero_dossier === 'T2-0001') || patients[0];
if (!patient) throw new Error('no isolated patient');

const browser = await chromium.launch({ headless: true });
const captures = [];
for (const viewport of [
  { width: 390, height: 844, label: '390x844' },
  { width: 768, height: 1024, label: '768x1024' },
  { width: 1280, height: 900, label: '1280x900' },
]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
  const response = await page.goto(`${appUrl}/patients/${patient.id}?tab=companion`, {
    waitUntil: 'networkidle',
    timeout: 90000,
  });
  await page.locator('[data-patient-companion-admin]').waitFor({ state: 'visible', timeout: 30000 });
  if (await page.locator('[data-pc08-staff-messaging]').count()) throw new Error('PC08 present in BEFORE');
  const horizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  const shot = `staff-before-${viewport.label}.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: true });
  const capture = {
    viewport,
    httpStatus: response?.status() ?? null,
    horizontalOverflow,
    pageErrors,
    consoleErrors,
    shot,
  };
  captures.push(capture);
  if (capture.httpStatus !== 200 || horizontalOverflow || pageErrors.length || consoleErrors.length) {
    throw new Error(`invalid staff BEFORE: ${JSON.stringify(capture)}`);
  }
  await context.close();
}
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify({
  productHead: process.env.PRODUCT_HEAD || null,
  patientId: patient.id,
  captures,
}, null, 2));
await browser.close();
await api.dispose();
