import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/g4-treasury-guard-after');
fs.mkdirSync(outDir, { recursive: true });

const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('T2_USER/T2_PASSWORD required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: user, password } });
if (!login.ok()) throw new Error('Treasury AFTER login failed');
const tokens = await login.json();
const headers = { Authorization: 'Bearer ' + tokens.access_token };
const patientsResponse = await api.get('/api/patients', { headers });
if (!patientsResponse.ok()) throw new Error('Treasury AFTER patient list failed');
const patient = (await patientsResponse.json()).find(row => row.numero_dossier === 'T2-0001');
if (!patient) throw new Error('Treasury AFTER fixture patient missing');

const browser = await chromium.launch({ headless: true });
const evidence = [];

for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 900 }]) {
  const context = await browser.newContext({ viewport, colorScheme: 'light' });
  const page = await context.newPage();
  await page.addInitScript(({ access, refresh }) => {
    localStorage.setItem('token', access);
    localStorage.setItem('refresh_token', refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: tokens.access_token, refresh: tokens.refresh_token });

  const pageErrors = [];
  const http5xx = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('response', response => {
    if (response.status() >= 500) http5xx.push({ status: response.status(), url: response.url() });
  });

  await page.goto(
    'http://127.0.0.1:5173/patients/' + patient.id + '?tab=admin&documentTab=honoraires',
    { waitUntil: 'networkidle', timeout: 90000 }
  );
  await page.getByRole('button', { name: /Échéances & options/i }).click();
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'visible', timeout: 10000 });

  const accountedLabel = page.getByText('Comptabiliser CA', { exact: true });
  await accountedLabel.locator('..').getByRole('button').click();
  await page.getByRole('button', { name: 'Partiel', exact: true }).click();

  const guard = page.getByRole('alert');
  await guard.waitFor({ state: 'visible', timeout: 5000 });
  const understood = page.getByRole('button', { name: 'Compris', exact: true });
  await understood.waitFor({ state: 'visible', timeout: 5000 });

  const hit = await page.evaluate(() => {
    const button = [...document.querySelectorAll('button')].find(el => el.textContent?.trim() === 'Compris');
    if (!(button instanceof HTMLElement)) return null;
    const rect = button.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    const top = document.elementFromPoint(x, y);
    return {
      buttonRect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
      topTag: top?.tagName || null,
      topText: top?.textContent?.trim().slice(0, 120) || null,
      buttonOwnsHit: top === button || Boolean(top && button.contains(top)),
    };
  });

  if (!hit?.buttonOwnsHit) throw new Error('Treasury AFTER Compris is not pointer-actionable at ' + viewport.width + 'x' + viewport.height);

  const screenshot = 'g4-honoraires-' + viewport.width + 'x' + viewport.height + '-treasury-partial-guard-after.png';
  await page.screenshot({ path: path.join(outDir, screenshot), fullPage: false, animations: 'disabled' });

  await understood.click();
  await guard.waitFor({ state: 'hidden', timeout: 5000 });
  await page.getByText('Encaissement', { exact: true }).waitFor({ state: 'visible', timeout: 5000 });

  const partielClass = await page.getByRole('button', { name: 'Partiel', exact: true }).getAttribute('class');
  if (partielClass?.includes('text-blue-600')) {
    throw new Error('Treasury AFTER accepted PARTIEL despite guard at ' + viewport.width + 'x' + viewport.height);
  }

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
  if (overflow) throw new Error('Treasury AFTER horizontal overflow at ' + viewport.width + 'x' + viewport.height);
  if (pageErrors.length) throw new Error('Treasury AFTER page errors at ' + viewport.width + 'x' + viewport.height + ': ' + pageErrors.join(' | '));
  if (http5xx.length) throw new Error('Treasury AFTER HTTP 5xx at ' + viewport.width + 'x' + viewport.height);

  evidence.push({ viewport, screenshot, hit, overflow, pageErrors, http5xx, guardDismissed: true, treasuryRemainedOpen: true, partialStatusAccepted: false });
  await context.close();
}

await browser.close();
await api.dispose();

const summary = { status: 'AFTER_PASS', viewports: evidence.length, evidence };
fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2));
console.log('G4_TREASURY_GUARD_AFTER ' + JSON.stringify({
  status: summary.status,
  viewports: summary.viewports,
  pointerActionable: evidence.map(row => ({ viewport: row.viewport, buttonOwnsHit: row.hit?.buttonOwnsHit ?? false })),
}));
