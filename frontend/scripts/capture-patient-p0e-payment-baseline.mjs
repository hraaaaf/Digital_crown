import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-p0e-payment-baseline');
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

async function openFinances(page) {
  await seedAuth(page);
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=finances`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Actes & Paiements', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
}

async function capture(kind, viewport) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const httpErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('response', response => {
    if (response.status() >= 400) httpErrors.push({ status: response.status(), url: response.url() });
  });
  await openFinances(page);

  if (kind === 'quickpay') {
    const open = page.getByRole('button', { name: /Enregistrer un paiement/i });
    await open.scrollIntoViewIfNeeded();
    await open.click();
    await page.getByRole('dialog', { name: 'Saisir un Paiement' }).waitFor({ state: 'visible' });
  } else {
    const pay = page.getByRole('button', { name: /^Payer$/i }).first();
    await pay.scrollIntoViewIfNeeded();
    await pay.click();
    await page.getByText('Paiement acte', { exact: true }).waitFor({ state: 'visible' });
  }

  const cash = page.getByRole('button', { name: /Espèces/i }).last();
  await cash.waitFor({ state: 'visible' });
  const cashClass = await cash.getAttribute('class');
  const cashSelected = Boolean(cashClass && cashClass.includes('border-primary') && cashClass.includes('text-primary'));
  const methods = ['Espèces', 'Carte', 'Virement', 'Chèque'];
  const methodStates = {};
  for (const label of methods) {
    const button = page.getByRole('button', { name: new RegExp(label, 'i') }).last();
    const className = await button.getAttribute('class');
    methodStates[label] = Boolean(className && className.includes('border-primary') && className.includes('text-primary'));
  }

  const metrics = await page.evaluate(() => ({
    pathname: location.pathname,
    search: location.search,
    noHorizontalOverflow: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
  }));
  const screenshot = `patient-p0e-${kind}-baseline-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });
  evidence.push({ kind, viewport, screenshot, cashSelected, methodStates, metrics, pageErrors, httpErrors });
  await context.close();
}

for (const viewport of viewports) {
  await capture('quickpay', viewport);
  await capture('payacte', viewport);
}

const relevantHttpErrors = evidence.flatMap(item => item.httpErrors.map(error => ({ kind: item.kind, viewport: item.viewport, ...error })))
  .filter(error => !/\/api\/patients\/\d+\/master-plan$/.test(error.url) || error.status !== 404);
const summary = {
  totalCaptures: evidence.length,
  implicitCashSelections: evidence.filter(item => item.cashSelected).map(item => ({ kind: item.kind, viewport: item.viewport })),
  unexpectedMultipleSelections: evidence.filter(item => Object.values(item.methodStates).filter(Boolean).length !== 1).map(item => ({ kind: item.kind, viewport: item.viewport, methodStates: item.methodStates })),
  overflowFindings: evidence.filter(item => !item.metrics.noHorizontalOverflow).map(item => ({ kind: item.kind, viewport: item.viewport })),
  pageErrorFindings: evidence.filter(item => item.pageErrors.length).map(item => ({ kind: item.kind, viewport: item.viewport, errors: item.pageErrors })),
  relevantHttpErrors,
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
if (summary.totalCaptures !== 8 || summary.implicitCashSelections.length !== 8 || summary.unexpectedMultipleSelections.length || summary.pageErrorFindings.length || summary.relevantHttpErrors.length) {
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
}
await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
