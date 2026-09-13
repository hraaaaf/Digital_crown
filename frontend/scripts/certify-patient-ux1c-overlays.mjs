import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/patient-ux1c-overlays');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 1280, height: 900 },
];

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', {
  form: { username: 't2-browser@cabinet.ma', password: process.env.T2_PASSWORD },
});
if (!login.ok()) throw new Error(`UX1-C login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const headers = { Authorization: `Bearer ${tokens.access_token}` };
const patients = await api.get('/api/patients', { headers });
if (!patients.ok()) throw new Error(`UX1-C patients failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find((row) => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('UX1-C fixture patient T2-0001 missing');

const browser = await chromium.launch({ headless: true });
const evidence = [];

for (const viewport of viewports) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  const patientUrl = `http://127.0.0.1:5173/patients/${patient.id}`;
  await page.goto(patientUrl, { waitUntil: 'networkidle', timeout: 90000 });
  await page.getByRole('button', { name: 'Vue d’ensemble', exact: true }).waitFor({ state: 'visible', timeout: 30000 });
  await page.waitForTimeout(400);

  const headerLauncher = page.locator('[data-ux1-c-crownbot-header]');
  const floatingLauncher = page.locator('[data-ux1-c-crownbot-floating]');
  const headerVisible = await headerLauncher.isVisible().catch(() => false);
  const floatingVisible = await floatingLauncher.isVisible().catch(() => false);
  const compact = viewport.width < 1024;

  if (compact && (!headerVisible || floatingVisible)) {
    throw new Error(`UX1-C launcher contract failed at ${viewport.width}: header=${headerVisible} floating=${floatingVisible}`);
  }
  if (!compact && (headerVisible || !floatingVisible)) {
    throw new Error(`UX1-C desktop launcher contract failed at ${viewport.width}: header=${headerVisible} floating=${floatingVisible}`);
  }

  const closedShot = `ux1c-closed-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, closedShot), fullPage: false });

  const opener = page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
  if (await opener.count() !== 1) throw new Error(`UX1-C visible CrownBot opener missing at ${viewport.width}`);
  await opener.click();
  const overlay = page.locator('[data-ux1-c-crownbot-overlay]');
  await overlay.waitFor({ state: 'visible', timeout: 15000 });
  await page.waitForTimeout(250);
  const box = await overlay.boundingBox();
  if (!box) throw new Error(`UX1-C overlay bounds missing at ${viewport.width}`);

  const withinViewport = box.x >= -1 && box.y >= -1 && box.x + box.width <= viewport.width + 1 && box.y + box.height <= viewport.height + 1;
  if (!withinViewport) throw new Error(`UX1-C overlay escaped viewport at ${viewport.width}: ${JSON.stringify(box)}`);
  if (compact && (box.width < viewport.width - 30 || box.height < viewport.height - 30)) {
    throw new Error(`UX1-C compact overlay not viewport-dominant at ${viewport.width}: ${JSON.stringify(box)}`);
  }

  const layering = await page.evaluate(() => {
    const overlayNode = document.querySelector('[data-ux1-c-crownbot-overlay]');
    const toasterNode = document.querySelector('[data-rht-toaster]');
    const z = (node) => node ? Number.parseInt(getComputedStyle(node).zIndex || '0', 10) || 0 : null;
    return {
      overlayZ: z(overlayNode),
      toasterZ: z(toasterNode),
      toasterPresent: Boolean(toasterNode),
    };
  });
  if (compact && layering.toasterPresent && (layering.toasterZ ?? 0) >= (layering.overlayZ ?? 0)) {
    throw new Error(`UX1-C toast must stay below CrownBot at ${viewport.width}: ${JSON.stringify(layering)}`);
  }

  const openShot = `ux1c-open-${viewport.width}x${viewport.height}.png`;
  await page.screenshot({ path: path.join(outDir, openShot), fullPage: false });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  if (overflow) throw new Error(`UX1-C horizontal overflow at ${viewport.width}`);

  evidence.push({ viewport, compact, headerVisible, floatingVisible, overlayBox: box, layering, closedShot, openShot, overflow, pageErrors });
  await context.close();
}

await browser.close();
await api.dispose();

const invalid = evidence.flatMap(row => row.pageErrors.map(error => ({ viewport: row.viewport, error })));
const summary = { status: evidence.length === 3 && invalid.length === 0 ? 'PASS' : 'FAIL', viewports, evidence, invalid };
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('PATIENT_UX1C_OVERLAYS', JSON.stringify(summary));
if (summary.status !== 'PASS') process.exit(1);
