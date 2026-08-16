import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/t2-browser');
fs.mkdirSync(outDir, { recursive: true });

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
if (!patient) throw new Error('T2 certification patient not found');

const browser = await chromium.launch({ headless: true });
const results = [];
const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  const url = `http://127.0.0.1:5173/patients/${patient.id}?tab=admin&doc=ordonnance`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Documents A5', { exact: true }).waitFor({ timeout: 30000 });
  await page.getByText('Ordonnance', { exact: true }).first().waitFor({ timeout: 30000 });

  const bodyMetrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    activePath: location.pathname + location.search,
  }));
  if (bodyMetrics.scrollWidth > bodyMetrics.clientWidth + 2) {
    throw new Error(`Horizontal overflow at ${viewport.width}: ${bodyMetrics.scrollWidth} > ${bodyMetrics.clientWidth}`);
  }

  const shot = `t2-${viewport.width}x${viewport.height}-ordonnance.png`;
  await page.screenshot({ path: path.join(outDir, shot), fullPage: true });

  for (const label of ['Certificat', 'Devis', 'Note Honoraires', 'Suivi Paiement', 'Document Libre', 'Compagnon Diagnostique', 'Ordonnance']) {
    const tab = page.getByText(label, { exact: true }).first();
    await tab.waitFor({ state: 'visible', timeout: 15000 });
    await tab.click();
    await page.waitForTimeout(150);
  }

  await page.getByText('Document Libre', { exact: true }).first().click();
  const editable = page.locator('textarea').first();
  if (await editable.count()) {
    await editable.fill('Certification T2 — modification rapide');
    await editable.fill('Certification T2 — modification rapide 2');
  }

  const previewButton = page.getByRole('button', { name: /aperçu|prévisual/i }).first();
  if (await previewButton.count()) {
    await previewButton.click();
    const dialog = page.getByRole('dialog').last();
    await dialog.waitFor({ state: 'visible', timeout: 30000 });
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'hidden', timeout: 10000 });
  }

  results.push({ viewport, ...bodyMetrics, screenshot: shot, ok: true });
  await context.close();
}

const darkContext = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' });
const darkPage = await darkContext.newPage();
await darkPage.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });
await darkPage.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=admin&doc=ordonnance`, { waitUntil: 'networkidle', timeout: 90000 });
await darkPage.getByText('Documents A5', { exact: true }).waitFor({ timeout: 30000 });
await darkPage.screenshot({ path: path.join(outDir, 't2-1280x900-dark.png'), fullPage: true });
await darkContext.close();

fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify({ patientId: patient.id, results }, null, 2));
await browser.close();
await api.dispose();
console.log(JSON.stringify({ status: 'PASS', patientId: patient.id, viewports: results.length }));
