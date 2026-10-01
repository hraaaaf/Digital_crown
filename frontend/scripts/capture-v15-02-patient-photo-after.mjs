import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/v15-02-photo-after');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 768, height: 900 },
  { width: 1280, height: 900 },
];

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error(`V15-02 AFTER login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };

const patients = await api.get('/api/patients/', { headers });
if (!patients.ok()) throw new Error(`V15-02 AFTER patients failed: ${patients.status()} ${await patients.text()}`);
const rows = await patients.json();
const patient = rows.find((row) => row.numero_dossier === 'T2-0001') || rows[0];
if (!patient) throw new Error('V15-02 AFTER requires at least one patient fixture');

const samplePng = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAASUlEQVR42u3PQQ0AIBDAsAP/nuGNAvZoFSzZOjNnyNi7dwfgUQIeJeBRAh4l4FECHiXgUQIeJeBRAh4l4FECHiXgUQIeJeBRAh4l4FHCB30Bf4Q3zAAAAABJRU5ErkJggg==',
  'base64',
);

const browser = await chromium.launch({ headless: true });
const evidence = [];
try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport, colorScheme: 'light' });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', error => pageErrors.push(String(error)));

    await page.goto(`http://127.0.0.1:5173/patients/${patient.id}/edit`, {
      waitUntil: 'networkidle',
      timeout: 90000,
    });
    await page.getByRole('heading', { name: 'Mise à jour', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await page.locator('[data-patient-photo-editor]').waitFor({ state: 'visible', timeout: 30000 });
    await page.getByRole('button', { name: 'Importer', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
    await page.getByRole('button', { name: 'Prendre une photo', exact: true }).waitFor({ state: 'visible', timeout: 30000 });

    const baseMetrics = await page.evaluate(() => ({
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      photoEditorWidth: document.querySelector('[data-patient-photo-editor]')?.getBoundingClientRect().width || 0,
    }));
    if (baseMetrics.horizontalOverflow) throw new Error(`${viewport.width}: base overflow ${baseMetrics.scrollWidth}>${baseMetrics.innerWidth}`);

    const baseShot = `after-edit-patient-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outDir, baseShot), fullPage: true });

    const input = page.getByLabel('Importer une photo du patient');
    await input.setInputFiles({
      name: 'patient.png',
      mimeType: 'image/png',
      buffer: samplePng,
    });
    const dialog = page.getByRole('dialog', { name: 'Recadrer la photo' });
    await dialog.waitFor({ state: 'visible', timeout: 30000 });
    await page.getByLabel('Zoom de la photo').waitFor({ state: 'visible', timeout: 30000 });
    await page.getByLabel('Position horizontale').waitFor({ state: 'visible', timeout: 30000 });
    await page.getByLabel('Position verticale').waitFor({ state: 'visible', timeout: 30000 });

    const dialogMetrics = await page.evaluate(() => ({
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
      dialogWidth: document.querySelector('[role="dialog"] > div')?.getBoundingClientRect().width || 0,
      innerWidth: window.innerWidth,
    }));
    if (dialogMetrics.horizontalOverflow) throw new Error(`${viewport.width}: crop overflow`);

    const cropShot = `after-crop-patient-${viewport.width}x${viewport.height}.png`;
    await page.screenshot({ path: path.join(outDir, cropShot), fullPage: false });

    if (pageErrors.length) throw new Error(`${viewport.width}: page errors: ${pageErrors.join(' | ')}`);
    evidence.push({ viewport, baseShot, cropShot, baseMetrics, dialogMetrics, pageErrors });
    await context.close();
  }
} finally {
  await browser.close();
  await api.dispose();
}

fs.writeFileSync(path.join(outDir, 'evidence.json'), JSON.stringify(evidence, null, 2));
console.log('V15_02_PHOTO_AFTER', JSON.stringify(evidence));
