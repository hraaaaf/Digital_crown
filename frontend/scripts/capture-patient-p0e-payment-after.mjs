import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-p0e-payment-after');
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

async function methodStates(page) {
  const states = {};
  for (const label of ['Espèces', 'Carte', 'Virement', 'Chèque']) {
    const button = page.getByRole('button', { name: new RegExp(label, 'i') }).last();
    const className = await button.getAttribute('class');
    states[label] = Boolean(className && className.includes('border-primary') && className.includes('text-primary'));
  }
  return states;
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
    await page.getByPlaceholder('0.00').fill('250');
  } else {
    const pay = page.getByRole('button', { name: /^Payer$/i }).first();
    await pay.scrollIntoViewIfNeeded();
    await pay.click();
    await page.getByText('Paiement acte', { exact: true }).waitFor({ state: 'visible' });
  }

  const initialMethodStates = await methodStates(page);
  const initialSelectedCount = Object.values(initialMethodStates).filter(Boolean).length;
  const submit = page.getByRole('button', { name: /^Encaisser$/i }).last();
  const submitDisabledBeforeChoice = await submit.isDisabled();

  const metrics = await page.evaluate(() => ({
    pathname: location.pathname,
    search: location.search,
    noHorizontalOverflow: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
  }));
  const screenshot = `patient-p0e-${kind}-after-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });

  const explicitChoiceLabel = kind === 'quickpay' ? 'Carte' : 'Virement';
  await page.getByRole('button', { name: new RegExp(explicitChoiceLabel, 'i') }).last().click();
  const afterChoiceStates = await methodStates(page);
  const selectedAfterChoice = Object.entries(afterChoiceStates).filter(([, selected]) => selected).map(([label]) => label);
  const submitEnabledAfterChoice = await submit.isEnabled();

  evidence.push({
    kind,
    viewport,
    screenshot,
    initialMethodStates,
    initialSelectedCount,
    submitDisabledBeforeChoice,
    explicitChoiceLabel,
    selectedAfterChoice,
    submitEnabledAfterChoice,
    metrics,
    pageErrors,
    httpErrors,
  });
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
  initialSelections: evidence.filter(item => item.initialSelectedCount !== 0).map(item => ({ kind: item.kind, viewport: item.viewport, states: item.initialMethodStates })),
  submitNotDisabledBeforeChoice: evidence.filter(item => !item.submitDisabledBeforeChoice).map(item => ({ kind: item.kind, viewport: item.viewport })),
  explicitChoiceFailures: evidence.filter(item => item.selectedAfterChoice.length !== 1 || item.selectedAfterChoice[0] !== item.explicitChoiceLabel || !item.submitEnabledAfterChoice)
    .map(item => ({ kind: item.kind, viewport: item.viewport, explicitChoiceLabel: item.explicitChoiceLabel, selectedAfterChoice: item.selectedAfterChoice, submitEnabledAfterChoice: item.submitEnabledAfterChoice })),
  overflowFindings: evidence.filter(item => !item.metrics.noHorizontalOverflow).map(item => ({ kind: item.kind, viewport: item.viewport })),
  pageErrorFindings: evidence.filter(item => item.pageErrors.length).map(item => ({ kind: item.kind, viewport: item.viewport, errors: item.pageErrors })),
  relevantHttpErrors,
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
if (summary.totalCaptures !== 8 || summary.initialSelections.length || summary.submitNotDisabledBeforeChoice.length || summary.explicitChoiceFailures.length || summary.pageErrorFindings.length || summary.relevantHttpErrors.length) {
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
}
await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
