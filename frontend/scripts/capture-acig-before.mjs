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
await page.waitForTimeout(1200);
const results = page.locator('[data-medication-catalog-results] button[data-presentation-id]');
const count = await results.count();
const shot = 'acig-before-1280x900.png';
await page.screenshot({ path: path.join(outDir, shot), fullPage: false });
fs.writeFileSync(path.join(outDir, 'acig-before.json'), JSON.stringify({ query: 'ACIG', suggestionCount: count, screenshot: shot }, null, 2));
console.log(JSON.stringify({ query: 'ACIG', suggestionCount: count }));
await browser.close();
await api.dispose();
