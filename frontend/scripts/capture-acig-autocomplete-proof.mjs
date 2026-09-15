import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

const outDir = path.resolve('../artifacts/ordonnance-fidelity-v3');
fs.mkdirSync(outDir, { recursive: true });
const password = process.env.T2_PASSWORD;
if (!password) throw new Error('T2_PASSWORD is required');

const api = await request.newContext({ baseURL: 'http://127.0.0.1:8005' });
const login = await api.post('/api/auth/login', { form: { username: 't2-browser@cabinet.ma', password } });
if (!login.ok()) throw new Error(`Login failed: ${login.status()} ${await login.text()}`);
const tokens = await login.json();
const patients = await api.get('/api/patients', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
if (!patients.ok()) throw new Error(`Patients fetch failed: ${patients.status()} ${await patients.text()}`);
const patient = (await patients.json()).find(p => p.numero_dossier === 'T2-0001');
if (!patient) throw new Error('T2 certification patient not found');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'light' });
const page = await context.newPage();
const pageErrors = [];
page.on('pageerror', error => pageErrors.push(String(error)));
await page.addInitScript(({ access, refresh }) => {
  localStorage.setItem('token', access);
  localStorage.setItem('refresh_token', refresh || '');
  localStorage.setItem('appMode', 'prod');
}, { access: tokens.access_token, refresh: tokens.refresh_token });

await page.goto(`http://127.0.0.1:5173/patients/${patient.id}?tab=admin&documentTab=ordonnance`, { waitUntil: 'networkidle', timeout: 90000 });
await page.locator('[data-prescription-intelligence-studio="v1"]').waitFor({ state: 'attached', timeout: 30000 });
const input = page.getByPlaceholder('NOM OU DCI DU MÉDICAMENT...').first();
await input.scrollIntoViewIfNeeded();
await input.fill('ACIG');

const results = page.locator('[data-medication-catalog-results]');
await results.waitFor({ state: 'visible', timeout: 30000 });
const buttons = results.locator('button[data-presentation-id]');
const count = await buttons.count();
if (count < 1) throw new Error('No medication catalog suggestions returned for ACIG');

const acigam = results.locator('button[data-catalog-source-id="ammps-rmmg-2026-01"]', { hasText: 'ACIGAM 200 MG' }).first();
if (!(await acigam.count())) throw new Error('AMMPS ACIGAM 200 MG suggestion not rendered');
const acigamText = (await acigam.innerText()).trim();
if (!/ACIDE TIAPROFENIQUE/i.test(acigamText)) throw new Error('ACIGAM DCI not rendered');
if (!/AMMPS/i.test(acigamText)) throw new Error('AMMPS provenance not rendered');
if (!/2026-01/i.test(acigamText)) throw new Error('AMMPS edition date not rendered');
if (pageErrors.length) throw new Error(`Page errors: ${pageErrors.join(' | ')}`);

await page.waitForTimeout(250);
const shot = 'acig-autocomplete-after-1280x900.png';
await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
fs.writeFileSync(path.join(outDir, 'acig-autocomplete-after.json'), JSON.stringify({
  query: 'ACIG',
  selected: false,
  suggestionCount: count,
  acigamText,
  sourceId: 'ammps-rmmg-2026-01',
  pageErrors,
  screenshot: shot,
}, null, 2));
console.log(JSON.stringify({ query: 'ACIG', selected: false, suggestionCount: count, sourceId: 'ammps-rmmg-2026-01' }));
await browser.close();
await api.dispose();
