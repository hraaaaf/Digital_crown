import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-p0d-output-baseline');
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

async function openClinical(page) {
  await seedAuth(page);
  await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=clinical`, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByText('Espace Clinique', { exact: true }).waitFor({ state: 'visible', timeout: 30000 });
}

async function snap(page, protocol, phase, viewport, pageErrors, httpErrors) {
  const focus = phase === 'result'
    ? page.getByText(/Proposition clinique à valider/).first()
    : page.locator('text=/Génération du Diagnostic Endodontique|Génération du diagnostic \+ plan de traitement|Protocole d.urgence en cours/').first();
  await focus.waitFor({ state: 'visible', timeout: 10000 });
  await focus.scrollIntoViewIfNeeded();
  await page.waitForTimeout(120);
  const metrics = await page.evaluate(() => ({
    pathname: location.pathname,
    search: location.search,
    noHorizontalOverflow: document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2,
    bodyText: (document.body.innerText || '').slice(0, 8000),
  }));
  const screenshot = `patient-p0d-${protocol}-${phase}-baseline-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false });
  evidence.push({ protocol, phase, viewport, screenshot, metrics, pageErrors: [...pageErrors], httpErrors: [...httpErrors] });
}

async function captureEndo(viewport) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const httpErrors = [];
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('response', r => { if (r.status() >= 400) httpErrors.push({ status: r.status(), url: r.url() }); });
  await openClinical(page);
  await page.getByRole('button', { name: /Endodontie/i }).click();
  await page.getByText('Symptomatologie et Douleur', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Douleur spontanée, nocturne, irradiante/i }).click();
  await page.getByText('Test de Vitalité Pulpaire (Froid/Électrique)', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Positif \(Exagérée, persistante\)/i }).click();
  await page.getByText('Signes Radiographiques', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Lésion radio-claire/i }).click();
  await snap(page, 'endo', 'calculating', viewport, pageErrors, httpErrors);
  await page.getByText(/Proposition clinique à valider/).waitFor({ state: 'visible', timeout: 10000 });
  await snap(page, 'endo', 'result', viewport, pageErrors, httpErrors);
  await context.close();
}

async function captureUrgence(viewport) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  const httpErrors = [];
  page.on('pageerror', e => pageErrors.push(String(e)));
  page.on('response', r => { if (r.status() >= 400) httpErrors.push({ status: r.status(), url: r.url() }); });
  await openClinical(page);
  await page.getByRole('button', { name: /Examen Clinique Complet/i }).click();
  await page.getByRole('button', { name: /Urgence \/ Douleur aiguë/i }).click();
  await page.getByText('Type de douleur / motif urgent', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Douleur dentaire intense \(pulpaire\)/i }).click();
  await page.getByText('Localisation de la douleur', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Maxillaire postérieur/i }).click();
  await page.getByText('Caractère de la douleur', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Spontanée, permanente, lancinante/i }).click();
  await page.getByText('Signes généraux associés', { exact: true }).waitFor();
  await page.getByRole('button', { name: /Fièvre/i }).click();
  await snap(page, 'urgence', 'calculating', viewport, pageErrors, httpErrors);
  await page.getByText(/Proposition clinique à valider/).waitFor({ state: 'visible', timeout: 10000 });
  await snap(page, 'urgence', 'result', viewport, pageErrors, httpErrors);
  await context.close();
}

for (const viewport of viewports) {
  await captureEndo(viewport);
  await captureUrgence(viewport);
}

const relevantHttpErrors = evidence.flatMap(e => e.httpErrors.map(err => ({ protocol: e.protocol, phase: e.phase, viewport: e.viewport, ...err })))
  .filter(e => !/\/api\/patients\/\d+\/master-plan$/.test(e.url) || e.status !== 404);
const summary = {
  totalCaptures: evidence.length,
  overflowFindings: evidence.filter(e => !e.metrics.noHorizontalOverflow).map(e => ({ protocol: e.protocol, phase: e.phase, viewport: e.viewport })),
  pageErrorFindings: evidence.filter(e => e.pageErrors.length).map(e => ({ protocol: e.protocol, phase: e.phase, viewport: e.viewport, errors: e.pageErrors })),
  relevantHttpErrors,
  dangerousOutputEvidence: evidence.filter(e => e.phase === 'result').map(e => ({
    protocol: e.protocol,
    viewport: e.viewport,
    hasPulpite: e.metrics.bodyText.includes('Pulpite Irréversible'),
    hasValidationBanner: e.metrics.bodyText.includes('Proposition clinique à valider'),
  })),
};
fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
if (summary.totalCaptures !== 16 || summary.overflowFindings.length || summary.pageErrorFindings.length || summary.relevantHttpErrors.length) {
  console.error(JSON.stringify(summary, null, 2));
  process.exit(1);
}
if (summary.dangerousOutputEvidence.some(e => !e.hasPulpite || !e.hasValidationBanner)) {
  console.error('Expected current authoritative output was not reproduced consistently.');
  console.error(JSON.stringify(summary.dangerousOutputEvidence, null, 2));
  process.exit(1);
}
await browser.close();
await api.dispose();
console.log(JSON.stringify(summary, null, 2));
