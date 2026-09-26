import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/v1-07-schema-open-tooth-proof');
fs.mkdirSync(outDir, { recursive: true });

const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password },
});
if (!login.ok()) throw new Error('login failed: ' + login.status() + ' ' + await login.text());
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };

const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error('patients failed: ' + patients.status());
const patient = (await patients.json()).find((row) => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('fixture T2-0001 missing');

const browser = await chromium.launch({ headless: true });
const viewports = [{ width: 390, height: 844 }, { width: 1280, height: 900 }];
const tabs = [
  ['devis', 'Devis'],
  ['honoraires', 'Note Honoraires'],
];
const proof = [];

async function seedAuth(page) {
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });
}

async function frameSchema(page, tabSlug, viewport, suffix) {
  const tooth11 = page.getByRole('button', { name: /^Dent 11(?:,|$)/ }).first();
  await tooth11.waitFor({ state: 'visible', timeout: 30000 });
  await tooth11.scrollIntoViewIfNeeded();
  await page.evaluate(() => window.scrollBy(0, -180));
  await page.waitForTimeout(250);
  const file = tabSlug + '-' + suffix + '-' + viewport.width + 'x' + viewport.height + '.png';
  await page.screenshot({
    path: path.join(outDir, file),
    fullPage: false,
    animations: 'disabled',
  });
  return file;
}

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await seedAuth(page);

  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  page.on('response', (r) => {
    if (r.status() >= 500) http5xx.push({ url: r.url(), status: r.status() });
  });

  const patientUrl = 'http://127.0.0.1:5173/patients/' + patient.id;

  for (const [tabSlug, tabLabel] of tabs) {
    await page.goto(patientUrl + '?tab=admin&documentTab=' + tabSlug, {
      waitUntil: 'networkidle',
      timeout: 90000,
    });

    const studio = page.getByLabel('Types de documents');
    await studio.waitFor({ state: 'visible', timeout: 30000 });
    await studio.getByRole('button', { name: tabLabel, exact: true }).waitFor({ state: 'visible', timeout: 30000 });

    const planButton = page.getByRole('button').filter({ hasText: 'Plan de soins' }).first();
    await planButton.waitFor({ state: 'visible', timeout: 30000 });

    const continueButton = page.getByRole('button', { name: /Continuer vers les prestations/i });
    if (!(await continueButton.count())) {
      await planButton.click();
      await continueButton.waitFor({ state: 'visible', timeout: 10000 });
    }

    await page.getByRole('button', { name: 'Adulte', exact: true }).click();
    await page.getByRole('button', { name: /Soins Ciblés \(1 Dent\)/i }).click();

    const tooth11 = page.getByRole('button', { name: /^Dent 11(?:,|$)/ }).first();
    await tooth11.waitFor({ state: 'visible', timeout: 30000 });

    const openFile = await frameSchema(page, tabSlug, viewport, 'schema-open');

    // Select one real FDI tooth without opening the treatment selector:
    // grouped mode preserves the whole odontogram so the selected state remains visually inspectable.
    await page.getByRole('button', { name: /Bridge & Prothèses/i }).click();
    await tooth11.focus();
    await tooth11.press('Enter');
    await page.waitForFunction(
      () => [...document.querySelectorAll('[role="button"][aria-label^="Dent 11"]')]
        .some((el) => el.getAttribute('aria-pressed') === 'true'),
      null,
      { timeout: 10000 },
    );

    const selectedFile = await frameSchema(page, tabSlug, viewport, 'tooth-11-selected');
    proof.push({
      viewport: viewport.width + 'x' + viewport.height,
      tab: tabSlug,
      openFile,
      selectedFile,
      tooth: 11,
      ariaPressed: await tooth11.getAttribute('aria-pressed'),
      overflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2),
    });
  }

  if (pageErrors.length) throw new Error('page errors: ' + JSON.stringify(pageErrors));
  if (http5xx.length) throw new Error('HTTP 5xx: ' + JSON.stringify(http5xx));
  await context.close();
}

await browser.close();
await api.dispose();

if (proof.some((p) => p.ariaPressed !== 'true')) throw new Error('FDI 11 selection not proven');
if (proof.some((p) => p.overflow)) throw new Error('horizontal overflow detected');

fs.writeFileSync(path.join(outDir, 'proof.json'), JSON.stringify({
  baseProductHead: '0354bf6828e98ec50ec7afdef95941f621eb335b',
  patient: 'T2-0001',
  proof,
}, null, 2));

console.log('SCHEMA_OPEN_TOOTH_PROOF', JSON.stringify(proof));
